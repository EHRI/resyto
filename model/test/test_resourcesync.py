#! /usr/bin/env python3
# -*- coding: utf-8 -*-
import logging
import os
import sys
import unittest

from model.resourcesync import ResourceSync
from util.observe import GreedyEventLogger


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
        rs.register(GreedyEventLogger(level=logging.INFO))

        generator = rs.resourcelist_generator()
        for count_resources, count_documents, rl in generator([os.path.join(user_home, "tmp/rs")]):
            rl.pretty_xml = True
            print("========\n", "count resources=%d, count_documents=%d\n" % (count_resources, count_documents),
                  rl.as_xml())

    def test_create_resourcelist_from_directory(self):
        user_home = os.path.expanduser("~")
        metadata_dir = os.path.join(user_home, "tmp", "rs", "metadata")
        rs = ResourceSync(resource_dir=user_home, metadata_dir=metadata_dir)
        #rs.register(GreedyEventLogger(level=logging.INFO))

        rs.max_items_in_list = 5

        rs.create_resourcelists_from_directories(os.path.join(user_home, "tmp/rs"))

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





