#! /usr/bin/env python3
# -*- coding: utf-8 -*-
import logging
import os
import re
from enum import Enum
from glob import glob

from model.executor_changelist import NewChangelistExecutor, IncrementalChangelistExecutor
from model.executor_resourcelist import ResourceListExecutor
from model.executors import ExecutorParameters, SitemapData
from model.rs_enum import Strategy, Capability
from resync import CapabilityList
from resync import ChangeList
from resync import Resource
from resync import ResourceList
from resync.list_base_with_index import ListBaseWithIndex
from resync.sitemap import Sitemap
from util import defaults
from util.observe import Observable

LOG = logging.getLogger(__name__)

CLASS_NAME_RESOURCE_GATE_BUILDER = "ResourceGateBuilder"


class ResourceSyncEvent(Enum):

    start_file_search = 0
    found_file = 1
    created_resource = 2
    completed_document = 3
    found_changes = 4


class ResourceSync(Observable, ExecutorParameters):

    def __init__(self, **kwargs):
        Observable.__init__(self)
        ExecutorParameters.__init__(self, **kwargs)

    def execute(self, filenames: iter):
        executor = None
        if self.__strategy__() == Strategy.new_resourcelist:
            executor = ResourceListExecutor(**self.__dict__)
        elif self.__strategy__() == Strategy.new_changelist:
            executor = NewChangelistExecutor(**self.__dict__)
        elif self.__strategy__() == Strategy.inc_changelist:
            executor = IncrementalChangelistExecutor(**self.__dict__)

        if executor:
            executor.register(*self.observers)
            executor.execute(filenames)
        else:
            raise NotImplementedError("Strategy not implemented: %s" % self.strategy)

    def assemble_sitemaps(self, sitemap_generator, capabilitylist=None):
        self.start_processing = defaults.w3c_now()
        sitemaps = []

        for sitemap_data, sitemap in sitemap_generator():
            sitemaps.append(sitemap_data)

        self.end_processing = defaults.w3c_now()

        if len(sitemaps) > 1:
            sitemaps = self.create_index(sitemaps)

        if len(sitemaps) == 1:
            if capabilitylist is None:
                capabilitylist = CapabilityList()

            resources_count = 0
            for sitemap_data in sitemaps:
                capabilitylist.add(Resource(uri=sitemap_data.url, capability=sitemap_data.capability_name))
                resources_count = sitemap_data.resources_count

            self.finish_sitemap(resources_count, 1, capabilitylist)
        return capabilitylist

    def create_index(self, sitemaps):
        if len(sitemaps) == 0:
            return []

        capability_name = sitemaps[0].capability_name
        if capability_name == "resourcelist":
            return self.create_resourcelist_index(sitemaps)
        elif capability_name == "changelist":
            return self.create_changelist_index(sitemaps)

    def create_resourcelist_index(self, sitemaps):
        rl_index = ResourceList()
        rl_index.sitemapindex = True
        rl_index.md_at = self.start_processing
        rl_index.md_completed = self.end_processing
        index_path = os.path.join(self.metadata_dir, "resourcelist-index" + ".xml")
        rel_index_path = os.path.relpath(index_path, self.resource_dir)
        index_url = self.url_prefix + defaults.sanitize_url_path(rel_index_path)
        rl_index.link_set(rel="up", href=self.current_capabilitylist_url())

        resources_count = 0
        for sitemap_data in sitemaps:
            rl_index.add(Resource(uri=sitemap_data.url, md_at=sitemap_data.md_at,
                                  md_completed=sitemap_data.md_completed))
            if sitemap_data.document_saved:
                self.update_rel_index(index_url, sitemap_data.path)
            resources_count = sitemap_data.resources_count

        sitemap_data = SitemapData(resources_count, 1, index_url, index_path, "resourcelist")
        if self.save_sitemaps:
            self.save_sitemap(rl_index, index_path)
            sitemap_data.document_saved = True

        self.observers_inform(self, ResourceSyncEvent.completed_document, document=rl_index, **sitemap_data.__dict__)
        return [sitemap_data]

    def create_changelist_index(self, sitemaps, ):
        raise NotImplementedError

    def resourcelist_generator(self, filenames: iter) -> iter:

        def generator() -> [SitemapData, ResourceList]:
            resourcelist = None
            document_count = self.list_ordinal(Capability.resourcelist.name)
            resource_count = 0
            resource_generator = self.resource_generator()
            for resource_count, resource in resource_generator(filenames):
                # stuff resource into resourcelist
                if resourcelist is None:
                    resourcelist = ResourceList()
                    resourcelist.md_at = defaults.w3c_now()

                resourcelist.add(resource)

                # under conditions: yield the current resourcelist
                if resource_count % self.max_items_in_list == 0:
                    document_count += 1
                    resourcelist.md_completed = defaults.w3c_now()
                    sitemap_data = self.finish_sitemap(resource_count, document_count, resourcelist)
                    yield sitemap_data, resourcelist
                    resourcelist = None

            # under conditions: yield the current and last resourcelist
            if resourcelist:
                document_count += 1
                resourcelist.md_completed = defaults.w3c_now()
                sitemap_data = self.finish_sitemap(resource_count, document_count, resourcelist)
                yield sitemap_data, resourcelist

        return generator

    def changelist_generator(self, filenames: iter) -> iter:

        def generator() -> [SitemapData, ChangeList]:
            resource_generator = self.resource_generator()
            self.update_previous_state()
            prev_r = self.previous_resources
            curr_r = {resource.uri: resource for count, resource in resource_generator(filenames)}
            created = [r for r in curr_r.values() if r.uri not in prev_r]
            updated = [r for r in curr_r.values() if r.uri in prev_r and r.md5 != prev_r[r.uri].md5]
            deleted = [r for r in prev_r.values() if r.uri not in curr_r]
            self.observers_inform(self, ResourceSyncEvent.found_changes, created=len(created), updated=len(updated),
                                  deleted=len(deleted))
            all_r = {"created": created, "updated": updated, "deleted": deleted}

            changelist = None
            document_count = self.list_ordinal(Capability.changelist.name)
            resource_count = 0
            for kv in all_r.items():
                for resource in kv[1]:
                    if changelist is None:
                        changelist = ChangeList()

                    resource.change = kv[0]
                    changelist.add(resource)
                    resource_count += 1

                    # under conditions: yield the current changelist
                    if resource_count % self.max_items_in_list == 0:
                        document_count += 1
                        sitemap_data = self.finish_sitemap(resource_count, document_count, changelist)
                        yield sitemap_data, changelist
                        changelist = None

            # under conditions: yield the current and last changelist
            if changelist:
                document_count += 1
                sitemap_data = self.finish_sitemap(resource_count, document_count, changelist)
                yield sitemap_data, changelist

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
                        self.observers_inform(self, ResourceSyncEvent.created_resource, resource=resource,
                                              count=count)
                    else:
                        LOG.debug("Rejected by resourcegate: %s" % file)
                else:
                    LOG.warn("Not a regular file: %s" % file)

        return generator

    def walk_directories(self, *directories) -> [str]:
        for directory in directories:
            abs_dir = os.path.abspath(directory)
            self.observers_inform(self, ResourceSyncEvent.start_file_search, directory=abs_dir)
            for root, _directories, _filenames in os.walk(abs_dir):
                for filename in _filenames:
                    file = os.path.join(root, filename)
                    self.observers_inform(self, ResourceSyncEvent.found_file, file=file)
                    yield file

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

        self.observers_inform(self, ResourceSyncEvent.completed_document, document=sitemap, **sitemap_data.__dict__)
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

    def update_previous_state(self):
        if self.previous_resources is None:
            self.previous_resources = {}

            # search for resourcelists
            resourcelist_files = sorted(glob(os.path.join(self.metadata_dir, "resourcelist_*.xml")))
            for rl_file_name in resourcelist_files:
                resourcelist = ResourceList()
                with open(rl_file_name, "r") as rl_file:
                    sm = Sitemap()
                    sm.parse_xml(rl_file, resources=resourcelist)

                self.md_from = resourcelist.md_at
                self.previous_resources.update({resource.uri: resource for resource in resourcelist.resources})

            # search for changelists
            changelist_files = sorted(glob(os.path.join(self.metadata_dir, "changelist_*.xml")))
            if self.strategy == Strategy.new_changelist and len(changelist_files) > 0:
                self.md_from = defaults.w3c_now()
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

                # ToDo change until value of existing changelists in another method. Not here.
                # if self.strategy == Strategy.new_changelist and self.save_sitemaps:
                #     changelist.md_until = self.md_from
                #     self.save_sitemap(changelist, cl_file_name)

        LOG.debug("Found %d resources in previous state." % len(self.previous_resources))

    def list_ordinal(self, capability):
        rs_files = sorted(glob(os.path.join(self.metadata_dir, capability + "*.xml")))
        if len(rs_files) == 0:
            return 0
        else:
            filename = os.path.basename(rs_files[len(rs_files) - 1])
            digits = re.findall("\d+", filename)
            return int(digits[0]) if len(digits) > 0 else 0

    def save_sitemap(self, sitemap, path):
        sitemap.pretty_xml = self.pretty_xml
        with open(path, "w") as sm_file:
            sm_file.write(sitemap.as_xml())

    def read_sitemap(self, path):
        with open(path, "r") as file:
            sm = Sitemap()
            sitemap = ListBaseWithIndex()
            sm.parse_xml(file, resources=sitemap)

        return sitemap

    def update_rel_index(self, index_url, path):
        sitemap = self.read_sitemap(path)
        sitemap.link_set(rel="index", href=index_url)
        self.save_sitemap(sitemap, path)





