#! /usr/bin/env python3
# -*- coding: utf-8 -*-
import logging
import os
import re
from collections import Iterator, Iterable
from enum import Enum
from glob import glob

from model.config import Configuration
from pluggable.gate import ResourceGateBuilder
from resync import CapabilityList
from resync import ChangeList
from resync import Resource
from resync import ResourceList
from resync.sitemap import Sitemap
from util import defaults
from util.gates import PluggedInGateBuilder
from util.observe import Observable

LOG = logging.getLogger(__name__)

CLASS_NAME_RESOURCE_GATE_BUILDER = "ResourceGateBuilder"


class ResourceSyncEvent(Enum):

    start_file_search = 0
    found_file = 1
    created_resource = 2
    completed_document = 3
    found_changes = 4


class Capability(Enum):

    resourcelist = 0
    changelist = 1
    resourcedump = 2
    changedump = 3
    resourcedump_manifest = 4
    changedump_manifest = 5
    capabilitylist = 6
    description = 7


class ResourceSync(Observable):

    def __init__(self, resource_dir=None, metadata_dir=None, url_prefix=None, plugin_dir=None):
        Observable.__init__(self)
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
        self.save_sitemaps = True
        self.capabilitylist_count = 0
        self.previous_resources = None

    def capabilitylist_generator(self):

        def generator(sitemap_generator, capabilitylist=None):

            for count_resources, count_docs, sitemap_url, sitemap in sitemap_generator():
                if capabilitylist is None:
                    capabilitylist = CapabilityList()
                    self.capabilitylist_count += 1

                capabilitylist.add_capability(sitemap, sitemap_url)

            if capabilitylist:
                uri = self.save_sitemap(self.capabilitylist_count, capabilitylist)
                yield uri, capabilitylist

        return generator

    def resourcelist_generator(self, filenames: iter) -> iter:

        def generator() -> [int, int, ResourceList]:
            resourcelist = None
            count_docs = self.list_ordinal(Capability.resourcelist.name)
            count_resources = 0
            resource_generator = self.resource_generator()
            for count_resources, resource in resource_generator(filenames):
                # stuff resource into resourcelist
                if resourcelist is None:
                    resourcelist = ResourceList()
                    resourcelist.md_at = defaults.w3c_now()

                resourcelist.add(resource)

                # under conditions: yield the current resourcelist
                if count_resources % self.max_items_in_list == 0:
                    count_docs += 1
                    resourcelist.md_completed = defaults.w3c_now()
                    uri = self.save_sitemap(count_docs, resourcelist)
                    yield count_resources, count_docs, uri, resourcelist
                    resourcelist = None

            # under conditions: yield the current and last resourcelist
            if resourcelist:
                count_docs += 1
                resourcelist.md_completed = defaults.w3c_now()
                uri = self.save_sitemap(count_docs, resourcelist)
                yield count_resources, count_docs, uri, resourcelist

        return generator

    def changelist_generator(self, filenames: iter) -> iter:

        def generator() -> [int, int, ChangeList]:
            resource_generator = self.resource_generator()
            prev = self.previous_state()
            curr = {resource.uri: resource for count, resource in resource_generator(filenames)}
            created = [r for r in curr.values() if r.uri not in prev]
            updated = [r for r in curr.values() if r.uri in prev and r.md5 != prev[r.uri].md5]
            deleted = [r for r in prev.values() if r.uri not in curr]
            self.update_observers(self, ResourceSyncEvent.found_changes, created=len(created), updated=len(updated),
                                  deleted=len(deleted))
            all_res = {"created": created, "updated": updated, "deleted": deleted}

            changelist = None
            count_docs = self.list_ordinal(Capability.changelist.name)
            count_resources = 0
            for kv in all_res.items():
                for resource in kv[1]:
                    if changelist is None:
                        changelist = ChangeList()

                    resource.change = kv[0]
                    changelist.add(resource)
                    count_resources += 1

                    # under conditions: yield the current changelist
                    if count_resources % self.max_items_in_list == 0:
                        count_docs += 1
                        uri = self.save_sitemap(count_docs, changelist)
                        yield count_resources, count_docs, uri, changelist
                        changelist = None

            # under conditions: yield the current and last changelist
            if changelist:
                count_docs += 1
                uri = self.save_sitemap(count_docs, changelist)
                yield count_resources, count_docs, uri, changelist

        return generator

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
                        self.update_observers(self, ResourceSyncEvent.created_resource, resource=resource,
                                              count=count)
                    else:
                        LOG.debug("Rejected by resourcegate: %s" % file)
                else:
                    LOG.warn("Not a regular file: %s" % file)

        return generator

    def walk_directories(self, *directories) -> [str]:
        for directory in directories:
            abs_dir = os.path.abspath(directory)
            self.update_observers(self, ResourceSyncEvent.start_file_search, directory=abs_dir)
            for root, _directories, _filenames in os.walk(abs_dir):
                for filename in _filenames:
                    file = os.path.join(root, filename)
                    self.update_observers(self, ResourceSyncEvent.found_file, file=file)
                    yield file

    def save_sitemap(self, count, sitemap) -> str:
        path = os.path.join(self.metadata_dir, sitemap.capability_name + "{0:03d}".format(count) + ".xml")
        rel_path = os.path.relpath(path, self.resource_dir)
        uri = self.url_prefix + defaults.sanitize_url_path(rel_path)

        sitemap.link_set(rel="up", href=self.current_rel_up_for(sitemap))
        sitemap.pretty_xml = self.pretty_xml
        if self.save_sitemaps:
            with open(path, "w") as sm_file:
                sm_file.write(sitemap.as_xml())

        self.update_observers(self, ResourceSyncEvent.completed_document, uri=uri, document=sitemap, count=count)
        return uri

    def current_rel_up_for(self, sitemap):
        if sitemap.capability_name == "capabilitylist":
            return self.current_description_url()
        else:
            return self.current_capabilitylist_url()

    def current_capabilitylist_url(self) -> str:
        path = os.path.join(self.metadata_dir, "capabilitylist" + "{0:03d}".format(self.capabilitylist_count) + ".xml")
        rel_path = os.path.relpath(path, self.resource_dir)
        return self.url_prefix + defaults.sanitize_url_path(rel_path)

    def current_description_url(self):
        path = os.path.join(self.metadata_dir, ".well-known", "resourcesync")
        rel_path = os.path.relpath(path, self.resource_dir)
        return self.url_prefix + defaults.sanitize_url_path(rel_path)

    def previous_state(self) -> [Resource]:
        if self.previous_resources is None:
            self.previous_resources = {}
            resourcelist_files = sorted(glob(os.path.join(self.metadata_dir, "resourcelist*.xml")))
            for rl_file_name in resourcelist_files:
                resourcelist = ResourceList()
                with open(rl_file_name, "r") as rl_file:
                    sm = Sitemap()
                    sm.parse_xml(rl_file, resources=resourcelist)
                    self.previous_resources.update({resource.uri: resource for resource in resourcelist.resources})

            changelist_files = sorted(glob(os.path.join(self.metadata_dir, "changelist*.xml")))
            for cl_file_name in changelist_files:
                changelist = ChangeList()
                with open(cl_file_name, "r") as cl_file:
                    sm = Sitemap()
                    sm.parse_xml(cl_file, resources=changelist)

                for resource in changelist.resources:
                    if resource.change == "created" or resource.change == "updated":
                        self.previous_resources.update({resource.uri: resource})
                    elif resource.change == "deleted" and resource.uri in self.previous_resources:
                        del self.previous_resources[resource.uri]

        LOG.debug("Found %d resources in previous state." % len(self.previous_resources))
        return self.previous_resources

    def list_ordinal(self, capability):
        rs_files = sorted(glob(os.path.join(self.metadata_dir, capability + "*.xml")))
        if len(rs_files) == 0:
            return 0
        else:
            filename = os.path.basename(rs_files[len(rs_files) - 1])
            digits = re.findall("\d+", filename)
            return int(digits[0]) if len(digits) > 0 else 0





