#! /usr/bin/env python3
# -*- coding: utf-8 -*-
import logging
import os
import urllib.parse

from model.config import Configuration
from model.filters import Filters, DirectoryPatternFilter, HiddenFileFilter
from resync import Resource
from resync import ResourceList
from resync.sitemap import Sitemap
from util import defaults


class ResourceSync(object):

    def __init__(self, resource_dir=None, metadata_dir=None, url_prefix=None, stop_on_error=False):
        self.logger = logging.getLogger(__name__)
        self.config = Configuration()
        self.resource_dir = self.config.core_resource_dir() if resource_dir is None else resource_dir
        self.metadata_dir = self.config.core_metadata_dir() if metadata_dir is None else metadata_dir
        defaults.sanitize_directory_path(self.resource_dir)
        self.url_prefix = self.config.core_url_prefix() if url_prefix is None else url_prefix
        defaults.sanitize_url_prefix(self.url_prefix)

        self.stop_on_error = stop_on_error

        self.file_filters = Filters()
        self.file_filters.including(
            DirectoryPatternFilter("^" + self.resource_dir)
        ).excluding(
            HiddenFileFilter(),
            DirectoryPatternFilter("^" + self.metadata_dir)
        )

        self.max_items_in_list = 50000

    def resourcelists_from_directory(self, directory):
        abs_dir = os.path.abspath(directory)
        filenames = []
        for root, _directories, _filenames in os.walk(abs_dir):
            for filename in _filenames:
                filenames.append(os.path.join(root, filename))

        return self.resourcelists_from_files(filenames)

    def resourcelists_from_files(self, filenames=list()):
        count_files = 0
        rl = None
        for filename in filenames:
            file_path = os.path.abspath(filename)
            if self.file_filters.accept(file_path):
                count_files += 1
                if (count_files -1) % self.max_items_in_list == 0:
                    if rl:
                        yield rl
                    rl = ResourceList()

                path = os.path.relpath(file_path, self.resource_dir)
                uri = self.url_prefix + urllib.parse.quote(path)
                stat = os.stat(file_path)
                rl.add(Resource(uri=uri, length=stat.st_size,
                                lastmod=defaults.w3c_datetime(stat.st_ctime),
                                md5=defaults.md5_for_file(file_path)))
        if rl:
            yield rl






