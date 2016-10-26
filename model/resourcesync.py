#! /usr/bin/env python3
# -*- coding: utf-8 -*-
import logging
import os
from collections import Iterator, Iterable
from enum import Enum

from model.config import Configuration
from pluggable.gate import ResourceGateBuilder
from resync import CapabilityList
from resync import Resource
from resync import ResourceList
from util import defaults
from util.gates import PluggedInGateBuilder
from util.observe import Observable

CLASS_NAME_RESOURCE_GATE_BUILDER = "ResourceGateBuilder"


class ResourceSyncEvent(Enum):

    completed_search = 0
    completed_document = 1
    created_resource = 2


class ResourceSync(Observable):

    def __init__(self, resource_dir=None, metadata_dir=None, url_prefix=None, plugin_dir=None):
        Observable.__init__(self)
        self.logger = logging.getLogger(__name__)
        self.config = Configuration()
        self.resource_dir = self.config.core_resource_dir() if resource_dir is None else resource_dir
        self.metadata_dir = self.config.core_metadata_dir() if metadata_dir is None else metadata_dir
        defaults.sanitize_directory_path(self.resource_dir)
        self.url_prefix = self.config.core_url_prefix() if url_prefix is None else url_prefix
        defaults.sanitize_url_prefix(self.url_prefix)
        self.plugin_dir = self.config.core_plugin_dir() if plugin_dir is None else plugin_dir
        if self.plugin_dir is "":
            self.plugin_dir = None

        default_builder = ResourceGateBuilder(self.resource_dir, self.metadata_dir, self.plugin_dir)
        gate_builder = PluggedInGateBuilder(CLASS_NAME_RESOURCE_GATE_BUILDER, default_builder, self.plugin_dir)
        self.passes_resourcegate = gate_builder.build_gate()

        self.max_items_in_list = 50000
        self.pretty_xml = True

    def create_resourcelists_from_directories(self, *directories):
        self.create_resourcelists_from_files(self.walk_directories(*directories))

    def create_resourcelists_from_files(self, filenames: iter):
        # should we empty the metadatadir?
        capa_path = os.path.join(self.metadata_dir, "capabilitylist.xml")
        capa_uri = self.url_prefix + defaults.sanitize_url_path(capa_path)
        capabilitylist = CapabilityList()

        count_lists = 0
        for resourcelist in self.list_resourcelists_from_files(filenames):
            count_lists += 1

            rl_path = os.path.join(self.metadata_dir, "resourcelist" + str(count_lists) + ".xml")
            resourcelist.pretty_xml = self.pretty_xml
            with open(rl_path, "w") as rl_file:
                rl_file.write(resourcelist.as_xml())
            self.logger.debug("Saved resourcelist: %s" % rl_path)

            path = os.path.relpath(rl_path, self.resource_dir)
            uri = self.url_prefix + defaults.sanitize_url_path(path)
            stat = os.stat(rl_path)
            resource = Resource(uri=uri, length=stat.st_size,
                                lastmod=defaults.w3c_datetime(stat.st_ctime),
                                md5=defaults.md5_for_file(rl_path))
            capabilitylist.add(resource)

        if count_lists > 1:
            pass
            ## create a resourcelistindex
            # rli_path = os.path.join(self.metadata_dir, "resourcelistindex.xml")
            # resourcelistindex.pretty_xml = self.pretty_xml
            # with open(rli_path, "w") as rli_file:
            #     rli_file.write(resourcelistindex.index_as_xml())
            # self.logger.debug("Saved resourcelistindex: %s" % rli_path)



    # def capabilitylist_generator(self):
    #
    #     def generator(filenames, kid_generator):
    #
    #

    def resourcelist_generator(self) -> iter:

        def generator(filenames: iter) -> [int, int, ResourceList]:
            resourcelist = None
            count = 0
            count_resources = 0
            resource_generator = self.resource_generator()
            for count_resources, resource in resource_generator(filenames):
                # stuff resource into resourcelist
                if resourcelist is None:
                    resourcelist = ResourceList()
                resourcelist.add(resource)

                # under conditions: yield the current resourcelist
                if count_resources % self.max_items_in_list == 0:
                    count += 1
                    yield count_resources, count, resourcelist
                    self.update_observers(self, ResourceSyncEvent.completed_document, document=resourcelist,
                                          count=count)
                    resourcelist = None

            # under conditions: yield the current and last resourcelist
            if resourcelist:
                count += 1
                yield count_resources, count, resourcelist
                self.update_observers(self, ResourceSyncEvent.completed_document, document=resourcelist,
                                      count=count)

        return generator

    def resource_generator(self) -> iter:

        def generator(filenames: iter, count=0) -> [int, Resource]:
            for filename in filenames:
                if not isinstance(filename, str):
                    self.logger.warn("Not a string: %s" % filename)
                    filename = str(filename)

                file = os.path.abspath(filename)
                if not os.path.exists(file):
                    self.logger.warn("File does not exist: %s" % file)
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
                                            md5=defaults.md5_for_file(file))
                        yield count, resource
                        self.update_observers(self, ResourceSyncEvent.created_resource, resource=resource,
                                              count=count)
                    else:
                        self.logger.debug("Rejected by resourcegate: %s" % file)
                else:
                    self.logger.warn("Not a regular file: %s" % file)

        return generator

    def walk_directories(self, *directories) -> [str]:
        for directory in directories:
            abs_dir = os.path.abspath(directory)
            self.logger.debug("Searching files in %s", abs_dir)
            for root, _directories, _filenames in os.walk(abs_dir):
                for filename in _filenames:
                    yield os.path.join(root, filename)







