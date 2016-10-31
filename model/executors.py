#! /usr/bin/env python3
# -*- coding: utf-8 -*-
import logging
import os
import re
from abc import ABCMeta, abstractmethod
from enum import Enum
from glob import glob

from model.config import Configuration
from model.rs_enum import Strategy
from pluggable.gate import ResourceGateBuilder
from resync import Resource
from resync.list_base_with_index import ListBaseWithIndex
from resync.sitemap import Sitemap
from util import defaults
from util.gates import PluggedInGateBuilder
from util.observe import Observable, ObserverInterruptException

LOG = logging.getLogger(__name__)

CLASS_NAME_RESOURCE_GATE_BUILDER = "ResourceGateBuilder"

WELL_KNOWN_PATH = ".well-known/resourcesync"


class ExecutorEvent(Enum):
    rejected_file = 0
    start_file_search = 1
    created_resource = 2
    completed_document = 3

    clear_metadata_directory = 100


class SitemapData(object):

    def __init__(self, resources_count=0, documents_count=0, url=None, path=None, capability_name=None,
                 document_saved=False):
        self.resources_count = resources_count
        self.documents_count = documents_count
        self.url = url
        self.path = path
        self.capability_name = capability_name
        self.document_saved = document_saved

        # resourcelist particulars: start and end date of processing
        self.md_at = None
        self.md_completed = None

    def __str__(self):
        return "%s, resources_count: %d, documents_count: %d, saved: %s\n\t  url: %s\n\t path: %s" \
               % (self.capability_name, self.resources_count, self.documents_count, str(self.document_saved),
                  self.url, self.path)


class ExecutorParameters(object):

    def __init__(self, **kwargs):
        config = Configuration()
        self.resource_dir = defaults.sanitize_directory_path(
            self.__arg__("resource_dir", config.core_resource_dir(), **kwargs))
        self.metadata_dir = self.__arg__("metadata_dir", config.core_metadata_dir(), **kwargs)
        self.strategy = self.__arg__("strategy", config.core_strategy(), **kwargs)
        self.__strategy__() # check conversion for Strategy
        self.url_prefix = defaults.sanitize_url_prefix(
            self.__arg__("url_prefix", config.core_url_prefix(), **kwargs))
        self.plugin_dir = self.__arg__("plugin_dir", config.core_plugin_dir(), **kwargs)
        if self.plugin_dir is "":
            self.plugin_dir = None

        self.passes_resourcegate = self.__arg__("passes_resourcegate", None, **kwargs)
        if self.passes_resourcegate is None:
            default_builder = ResourceGateBuilder(self.resource_dir, self.__metadata_dir__(), self.plugin_dir)
            gate_builder = PluggedInGateBuilder(CLASS_NAME_RESOURCE_GATE_BUILDER, default_builder, self.plugin_dir)
            self.passes_resourcegate = gate_builder.build_gate()

        self.max_items_in_list = self.__arg__("max_items_in_list", 50000, **kwargs)
        self.pretty_xml = self.__arg__("pretty_xml", True, **kwargs)
        self.save_sitemaps = self.__arg__("save_sitemaps", True, **kwargs)

    def __arg__(self, name, default, **kwargs):
        value = default
        if name in kwargs and kwargs[name] is not None:
                value = kwargs[name]
        return value

    def __metadata_dir__(self):
        return os.path.join(self.resource_dir, self.metadata_dir)

    def __strategy__(self):
        return Strategy.strategy_for(self.strategy)


class Executor(Observable, ExecutorParameters, metaclass=ABCMeta):

    def __init__(self, **kwargs):
        Observable.__init__(self)
        ExecutorParameters.__init__(self, **kwargs)

    def execute(self, filenames: iter):
        if not os.path.exists(self.__metadata_dir__()):
            os.makedirs(self.__metadata_dir__())

        self.prepare_metadata_dir()
        self.generate_rs_documents(filenames)

    def prepare_metadata_dir(self):
        pass

    @abstractmethod
    def generate_rs_documents(self, filenames: iter):
        raise NotImplementedError

    def clear_metadata_dir(self):
        ok = self.observers_confirm(self, ExecutorEvent.clear_metadata_directory, metadata_dir=self.__metadata_dir__())
        if not ok:
            raise ObserverInterruptException(ExecutorEvent.clear_metadata_directory, self.__metadata_dir__())
        xml_files = glob(os.path.join(self.__metadata_dir__(), "*.xml"))
        for xml_file in xml_files:
            os.remove(xml_file)

        wellknown = os.path.join(self.__metadata_dir__(), WELL_KNOWN_PATH)
        if os.path.exists(wellknown):
            os.remove(wellknown)

    def resource_generator(self) -> iter:

        def generator(filenames: iter, count=0) -> [int, Resource]:
            for filename in filenames:
                if not isinstance(filename, str):
                    LOG.warn("Not a string: %s" % filename)
                    filename = str(filename)

                file = os.path.abspath(filename)
                if not os.path.exists(file):
                    LOG.warn("File does not exist: %s" % file)
                elif os.path.isdir(file):
                    for cr, rsc in generator(self.walk_directories(file), count=count):
                        yield cr, rsc
                        count = cr
                elif os.path.isfile(file):
                    if self.passes_resourcegate(file):
                        count += 1
                        path = os.path.relpath(file, self.resource_dir)
                        uri = self.url_prefix + defaults.sanitize_url_path(path)
                        stat = os.stat(file)
                        resource = Resource(uri=uri, length=stat.st_size,
                                            lastmod=defaults.w3c_datetime(stat.st_ctime),
                                            md5=defaults.md5_for_file(file),
                                            mime_type=defaults.mime_type(file))
                        yield count, resource
                        self.observers_inform(self, ExecutorEvent.created_resource, resource=resource,
                                              count=count)
                    else:
                        self.observers_inform(self, ExecutorEvent.rejected_file, file=file)
                else:
                    LOG.warn("Not a regular file: %s" % file)

        return generator

    def walk_directories(self, *directories) -> [str]:
        for directory in directories:
            abs_dir = os.path.abspath(directory)
            self.observers_inform(self, ExecutorEvent.start_file_search, directory=abs_dir)
            for root, _directories, _filenames in os.walk(abs_dir):
                for filename in _filenames:
                    file = os.path.join(root, filename)
                    yield file

    def list_ordinal(self, capability):
        rs_files = sorted(glob(os.path.join(self.__metadata_dir__(), capability + "_*.xml")))
        if len(rs_files) == 0:
            return 0
        else:
            filename = os.path.basename(rs_files[len(rs_files) - 1])
            digits = re.findall("\d+", filename)
            return int(digits[0]) if len(digits) > 0 else 0

    def finish_sitemap(self, resource_count, document_count, sitemap) -> SitemapData:
        capability_name = sitemap.capability_name
        path = os.path.join(self.metadata_dir, capability_name + "_{0:03d}".format(document_count) + ".xml")
        rel_path = os.path.relpath(path, self.resource_dir)
        url = self.url_prefix + defaults.sanitize_url_path(rel_path)
        sitemap.link_set(rel="up", href=self.current_rel_up_for(sitemap))
        sitemap_data = SitemapData(resource_count, document_count, url, path, capability_name)

        if capability_name == "resourcelist":
            sitemap_data.md_at = sitemap.md_at
            sitemap_data.md_completed = sitemap.md_completed

        if self.save_sitemaps:
            sitemap.pretty_xml = self.pretty_xml
            with open(path, "w") as sm_file:
                sm_file.write(sitemap.as_xml())
            sitemap_data.document_saved = True

        self.observers_inform(self, ExecutorEvent.completed_document, document=sitemap, **sitemap_data.__dict__)
        return sitemap_data

    def current_rel_up_for(self, sitemap):
        if sitemap.capability_name == "capabilitylist":
            return self.current_description_url()
        else:
            return self.current_capabilitylist_url()

    def current_capabilitylist_url(self) -> str:
        path = os.path.join(self.metadata_dir, "capabilitylist_" + "{0:03d}".format(1) + ".xml")
        rel_path = os.path.relpath(path, self.resource_dir)
        return self.url_prefix + defaults.sanitize_url_path(rel_path)

    def current_description_url(self):
        path = os.path.join(self.metadata_dir, ".well-known", "resourcesync")
        rel_path = os.path.relpath(path, self.resource_dir)
        return self.url_prefix + defaults.sanitize_url_path(rel_path)

    def update_rel_index(self, index_url, path):
        sitemap = self.read_sitemap(path)
        sitemap.link_set(rel="index", href=index_url)
        self.save_sitemap(sitemap, path)

    def save_sitemap(self, sitemap, path):
        sitemap.pretty_xml = self.pretty_xml
        with open(path, "w") as sm_file:
            sm_file.write(sitemap.as_xml())

    def read_sitemap(self, path, sitemap=None):
        if sitemap is None:
            sitemap = ListBaseWithIndex()
        with open(path, "r") as file:
            sm = Sitemap()
            sm.parse_xml(file, resources=sitemap)
        return sitemap
