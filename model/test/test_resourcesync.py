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
        # rs.register(GreedyEventLogger(level=logging.INFO))

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
        rs.register(EventLogger(logging_level=logging.INFO))

        generator1 = rs.resourcelist_generator([os.path.join(user_home, "tmp/rs")])
        generator2 = rs.resourcelist_generator([os.path.join(user_home, "tmp/rs/collection3")])

        for count_resources, count_documents, uri, rlist in generator1():
            rlist.pretty_xml = True
            print("========\n", "count resources=%d, count_documents=%d uri=%s\n"
                  % (count_resources, count_documents, uri),
                  rlist.as_xml())

        time.sleep(10)

        for count_resources, count_documents, uri, rlist in generator2():
            rlist.pretty_xml = True
            print("========\n", "count resources=%d, count_documents=%d uri=%s\n"
                  % (count_resources, count_documents, uri),
                  rlist.as_xml())

    def test_capabilitylist_generator_with_resourcelist(self):
        user_home = os.path.expanduser("~")
        metadata_dir = os.path.join(user_home, "tmp", "rs", "metadata")
        plugin_dir = os.path.join(user_home, "tmp", "rs", "plugins")
        # plugin_dir = None
        rs = ResourceSync(resource_dir=user_home, metadata_dir=metadata_dir, plugin_dir=plugin_dir)
        rs.max_items_in_list = 5
        rs.register(EventLogger(logging_level=logging.INFO, event_level=3))

        list_generator = rs.resourcelist_generator([os.path.join(user_home, "tmp/rs")])
        generator = rs.capabilitylist_generator()
        for uri, li in generator(list_generator):
            li.pretty_xml = True
            print(uri + "\n" + li.as_xml())

    def test_capabilitylist_generator_with_changelist(self):
        user_home = os.path.expanduser("~")
        metadata_dir = os.path.join(user_home, "tmp", "rs", "metadata")
        plugin_dir = os.path.join(user_home, "tmp", "rs", "plugins")

        rs = ResourceSync(resource_dir=user_home, metadata_dir=metadata_dir, plugin_dir=plugin_dir)
        rs.max_items_in_list = 5
        rs.register(EventLogger(logging_level=logging.INFO, event_level=3))

        list_generator = rs.changelist_generator([os.path.join(user_home, "tmp/rs")])
        generator = rs.capabilitylist_generator()
        for uri, li in generator(list_generator):
            li.pretty_xml = True
            print(uri + "\n" + li.as_xml())


    def test_previous_state_resources(self):
        user_home = os.path.expanduser("~")
        metadata_dir = os.path.join(user_home, "tmp", "rs", "metadata")
        rs = ResourceSync(resource_dir=user_home, metadata_dir=metadata_dir)

        resources = rs.previous_state()


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





