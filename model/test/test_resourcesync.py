#! /usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import unittest

from model.resourcesync import ResourceSync


class TestResourceSync(unittest.TestCase):

    def test_resourcelist_from_directory(self):
        user_home = os.path.expanduser("~")
        metadata_dir = os.path.join(user_home, "tmp", "rs", "metadata")
        rs = ResourceSync(resource_dir=user_home, metadata_dir=metadata_dir)
        # rs.file_filters.remove(rs.file_filters.filters[0]) # remove the HiddenFileFilter

        rl = rs.resourcelist_from_directory(os.path.join(user_home, "tmp"))
        print(rl.as_xml())
