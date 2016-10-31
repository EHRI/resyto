#! /usr/bin/env python3
# -*- coding: utf-8 -*-
import logging
import os
import sys
import unittest

import time

from model.resourcesync import ResourceSync
from resync import ChangeList
from resync.sitemap import Sitemap
from util.observe import EventLogger


@unittest.skip
class TestResourceSync(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        root = logging.getLogger()
        root.setLevel(logging.DEBUG)

        ch = logging.StreamHandler(sys.stdout)
        ch.setLevel(logging.DEBUG)
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(name)s - %(message)s')
        ch.setFormatter(formatter)
        root.addHandler(ch)

    def test_resource_generator(self):
        user_home = os.path.expanduser("~")
        metadata_dir = os.path.join(user_home, "tmp", "rs", "metadata")
        plugin_dir = os.path.join(user_home, "tmp", "rs", "plugins")
        rs = ResourceSync(resource_dir=user_home, metadata_dir=metadata_dir, plugin_dir=plugin_dir)
        rs.register(EventLogger(logging_level=logging.INFO))

        generator = rs.resource_generator()
        for count, resource in generator([os.path.join(user_home, "tmp/rs"), ["foo"], "bar", 6, None, "."]):
            print(count, resource)

    def test_resourcelist_generator(self):
        user_home = os.path.expanduser("~")
        metadata_dir = os.path.join(user_home, "tmp", "rs", "metadata")
        plugin_dir = os.path.join(user_home, "tmp", "rs", "plugins")
        #plugin_dir = None
        rs = ResourceSync(resource_dir=user_home, metadata_dir=metadata_dir, plugin_dir=plugin_dir)
        rs.max_items_in_list = 5
        #rs.register(EventLogger(logging_level=logging.INFO, event_level=3))

        generator1 = rs.resourcelist_generator([os.path.join(user_home, "tmp/rs")])
        generator2 = rs.resourcelist_generator([os.path.join(user_home, "tmp/rs/collection3")])

        for sitemap_data, rlist in generator1():
            rlist.pretty_xml = True
            print("========\n", sitemap_data, "\n",
                  rlist.as_xml())

        time.sleep(10)

        for sitemap_data, rlist in generator2():
            rlist.pretty_xml = True
            print("========\n", sitemap_data, "\n",
                  rlist.as_xml())

    def test_assemble_sitemaps_with_resourcelist_generator(self):
        user_home = os.path.expanduser("~")
        metadata_dir = os.path.join(user_home, "tmp", "rs", "metadata")
        plugin_dir = os.path.join(user_home, "tmp", "rs", "plugins")
        # plugin_dir = None
        rs = ResourceSync(resource_dir=user_home, metadata_dir=metadata_dir, plugin_dir=plugin_dir)
        rs.max_items_in_list = 5
        #rs.save_sitemaps = False
        rs.register(EventLogger(logging_level=logging.INFO, event_level=3))

        list_generator = rs.resourcelist_generator([os.path.join(user_home, "tmp/rs")])

        capabilitylist = rs.assemble_sitemaps(list_generator)

    def test_read_save_sitemap(self):
        rs = ResourceSync()
        path = "/Users/ecco/tmp/rs/metadata/resourcelist001.xml"

        sitemap = rs.read_sitemap(path)
        sitemap.pretty_xml = True
        xml1 = sitemap.as_xml()

        rs.save_sitemap(sitemap, path)
        sitemap = rs.read_sitemap(path)
        sitemap.pretty_xml = True
        xml2 = sitemap.as_xml()

        self.assertEqual(xml1, xml2)


    def test_previous_state_resources(self):
        user_home = os.path.expanduser("~")
        metadata_dir = os.path.join(user_home, "tmp", "rs", "metadata")
        rs = ResourceSync(resource_dir=user_home, metadata_dir=metadata_dir)

        rs.update_previous_state()
        print(rs.previous_resources)
        print(rs.md_from)


    def test_changelist_generator(self):
        user_home = os.path.expanduser("~")
        metadata_dir = os.path.join(user_home, "tmp", "rs", "metadata")
        plugin_dir = os.path.join(user_home, "tmp", "rs", "plugins")
        rs = ResourceSync(resource_dir=user_home, metadata_dir=metadata_dir, plugin_dir=plugin_dir)

        generator = rs.changelist_generator([os.path.join(user_home, "tmp/rs")])
        for x in generator():
            pass

    def test_stupid_changelist(self):
        path = "/Users/ecco/tmp/rs/metadata/changelist001.xml"
        with open(path, "r") as cl_file:
            changelist = ChangeList()
            sm = Sitemap()
            sm.parse_xml(cl_file, resources=changelist)

        changelist.pretty_xml = True
        print(changelist.as_xml())



    # keeping count in recursive loop and yielding things...
    def dingdong(self, dinges):

        def loop(dings, count=0):
            for ding in dings:
                if ding % 2 == 0:
                    count += 1
                    yield(count, ding)
                else:
                    # uneven number in next loop will cause infinite recursion!
                    for c, d in loop([100, 102], count):
                        yield c, d
                        count = c
        for c, d in loop(dinges):
            yield c, d

    def test_dingdong(self):
        dinges = [1, 2, 3, 4, 5]
        for count, ding in self.dingdong(dinges):
            print(count, ding)

    def dingdang(self):

        def loop(dings, count=0):
            for ding in dings:
                if ding % 2 == 0:
                    count += 1
                    yield(count, ding)
                else:
                    # uneven number in next loop will cause infinite recursion!
                    for c, d in loop([100, 102], count):
                        yield c, d
                        count = c

        return loop

    def test_dingdang(self):
        dinges = [1, 2, 3, 4, 5]
        loop = self.dingdang()
        for count, ding in loop(dinges):
            print(count, ding)





