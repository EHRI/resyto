#! /usr/bin/env python3
# -*- coding: utf-8 -*-
import logging
import os
import urllib.parse
from enum import Enum

from model.config import Configuration
from resync import Resource
from resync import ResourceList
from util import defaults
from util.filters import Filters, DirectoryPatternFilter, HiddenFileFilter, FilterBuilder
from util.observe import Observable


class ResourceSyncEvent(Enum):

    completed_search = 0
    completed_document = 1
    created_resource = 2


class ResourceFilterBuilder(FilterBuilder):

    def build_filters(self, filters, resourcesync=None, *kwargs):
        return filters


class ResourceSync(Observable):

    def __init__(self, resource_dir=None, metadata_dir=None, url_prefix=None):
        Observable.__init__(self)
        self.logger = logging.getLogger(__name__)
        self.config = Configuration()
        self.resource_dir = self.config.core_resource_dir() if resource_dir is None else resource_dir
        self.metadata_dir = self.config.core_metadata_dir() if metadata_dir is None else metadata_dir
        defaults.sanitize_directory_path(self.resource_dir)
        self.url_prefix = self.config.core_url_prefix() if url_prefix is None else url_prefix
        defaults.sanitize_url_prefix(self.url_prefix)

        self.file_filters = Filters()
        self.file_filters.add_including(
            DirectoryPatternFilter("^" + self.resource_dir)
        )
        self.file_filters.add_excluding(
            HiddenFileFilter(),
            DirectoryPatternFilter("^" + self.metadata_dir)
        )

        self.max_items_in_list = 50000

    def add_including_filters(self, *filters):
        self.file_filters.add_including(*filters)

    def add_excluding_filters(self, *filters):
        self.file_filters.add_excluding(*filters)

    def resourcelists_from_directories(self, *directories):
        filenames = []
        for directory in directories:
            abs_dir = os.path.abspath(directory)

            for root, _directories, _filenames in os.walk(abs_dir):
                for filename in _filenames:
                    filenames.append(os.path.join(root, filename))

        self.update_observers(self, ResourceSyncEvent.completed_search,
                              directories=directories, filenames=filenames)
        return self.resourcelists_from_files(filenames)

    def resourcelists_from_files(self, filenames=list()):
        count_files = 0
        count_documents = 0
        rl = None
        for filename in filenames:
            file_path = os.path.abspath(filename)
            if self.file_filters.accept(file_path):
                count_files += 1
                if (count_files -1) % self.max_items_in_list == 0:
                    if rl:
                        count_documents += 1
                        self.update_observers(self, ResourceSyncEvent.completed_document, document=rl, count=count_documents)
                        yield rl
                    rl = ResourceList()

                path = os.path.relpath(file_path, self.resource_dir)
                uri = self.url_prefix + urllib.parse.quote(path)
                stat = os.stat(file_path)
                resource = Resource(uri=uri, length=stat.st_size,
                                lastmod=defaults.w3c_datetime(stat.st_ctime),
                                md5=defaults.md5_for_file(file_path))
                rl.add(resource)
                self.update_observers(self, ResourceSyncEvent.created_resource, resource=resource, count=count_files)
        if rl:
            count_documents += 1
            self.update_observers(self, ResourceSyncEvent.completed_document, document=rl, count=count_documents)
            yield rl






