#! /usr/bin/env python3
# -*- coding: utf-8 -*-
import os

from model.executors import Executor, SitemapData, ExecutorEvent
from model.rs_enum import Capability
from resync import CapabilityList
from resync import Resource
from resync import ResourceList
from util import defaults

RESOURCELIST = "resourcelist"


class ResourceListExecutor(Executor):
    """ Executes the new resourcelist strategy.
    A ResourceListExecutor on execute clears the metadata directory and creates new resourcelist(s) for
    selected resources.
    """

    def prepare_metadata_dir(self):
        if self.save_sitemaps:
            self.clear_metadata_dir()

    def generate_rs_documents(self, filenames: iter):
        capabilitylist = None
        start_processing = defaults.w3c_now()
        sitemaps = []
        generator = self.resourcelist_generator(filenames)
        for sitemap_data, sitemap in generator():
            sitemaps.append(sitemap_data)

        end_processing = defaults.w3c_now()
        if len(sitemaps) > 1:
            sitemaps = self.create_index(sitemaps, start_processing, end_processing)

        if len(sitemaps) == 1:
            capabilitylist = CapabilityList()

            resources_count = 0
            for sitemap_data in sitemaps:
                capabilitylist.add(Resource(uri=sitemap_data.url, capability=sitemap_data.capability_name))
                resources_count = sitemap_data.resources_count

            self.finish_sitemap(resources_count, 1, capabilitylist)
        return capabilitylist

    def create_index(self, sitemaps, start_processing, end_processing):
        if len(sitemaps) == 0:
            return []

        rl_index = ResourceList()
        rl_index.sitemapindex = True
        rl_index.md_at = start_processing
        rl_index.md_completed = end_processing
        index_path = os.path.join(self.__metadata_dir__(), RESOURCELIST + "-index" + ".xml")
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

        sitemap_data = SitemapData(resources_count, 1, index_url, index_path, RESOURCELIST)
        if self.save_sitemaps:
            self.save_sitemap(rl_index, index_path)
            sitemap_data.document_saved = True

        self.observers_inform(self, ExecutorEvent.completed_document, document=rl_index, **sitemap_data.__dict__)
        return [sitemap_data]

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
