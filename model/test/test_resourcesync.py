#! /usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import unittest

from model.resourcesync import ResourceSync, ResourceSyncEvent
from util.filters import HiddenFileFilter, DirectoryPatternFilter
from util.observe import SelectiveEventPrinter


class TestResourceSync(unittest.TestCase):

    def test_resourcelist_from_directory(self):
        user_home = os.path.expanduser("~")
        metadata_dir = os.path.join(user_home, "tmp", "rs", "metadata")
        rs = ResourceSync(resource_dir=user_home, metadata_dir=metadata_dir)
        self.assertEquals(len(rs.file_filters.excluding_filters), 2)
        rs.file_filters.excluding_filters.clear()
        self.assertEquals(len(rs.file_filters.excluding_filters), 0)
        rs.add_excluding_filters(
            HiddenFileFilter(),
            DirectoryPatternFilter("^" + rs.metadata_dir)
        )
        self.assertEquals(len(rs.file_filters.excluding_filters), 2)

        # rs.file_filters.remove(rs.file_filters.filters[0]) # remove the HiddenFileFilter
        rs.max_items_in_list = 5
        rs.register(SelectiveEventPrinter(ResourceSyncEvent.completed_document, ResourceSyncEvent.completed_search))
        # rs.register(GreedyEventLogger(level=logging.WARN))
        # rs.register(SelectiveEventLogger(ResourceSyncEvent.completed_document, ResourceSyncEvent.completed_search, level=logging.WARN))

        for rl in rs.resourcelists_from_directories(os.path.join(user_home, "tmp/rs"), os.path.join(user_home, "tmp/test")):
            rl.pretty_xml = True
            print(rl.as_xml())
