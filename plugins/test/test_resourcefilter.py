#! /usr/bin/env python3
# -*- coding: utf-8 -*-
import inspect
import logging
import os
import unittest

import sys

from plugins.resourcefilter import ResourceGateBuilder, DefaultResourceGateBuilder, directory_pattern_predicate, \
    last_modified_after_predicate


class TestDefaultResourceGateBuilder(unittest.TestCase):

    def test_init_(self):
        root = logging.getLogger()
        root.setLevel(logging.DEBUG)

        ch = logging.StreamHandler(sys.stdout)
        ch.setLevel(logging.DEBUG)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        ch.setFormatter(formatter)
        root.addHandler(ch)

        builder = DefaultResourceGateBuilder("/Users/ecco/tmp/plugins")
        rgate = builder.build()
        print(rgate)
        print(inspect.getsource(rgate))


class TestPredicates(unittest.TestCase):

    def test_directory_pattern_filter_empty(self):
        dpf = directory_pattern_predicate() # should pass all strings
        self.assertTrue(dpf(""))
        self.assertTrue(dpf("."))
        self.assertTrue(dpf("\n"))
        self.assertTrue(dpf("foo"))

        self.assertFalse(dpf(None))
        self.assertFalse(dpf(42))
        self.assertFalse(dpf(self))

    def test_directory_pattern_filter(self):
        dpf = directory_pattern_predicate("abc")
        self.assertTrue(dpf("foo/babcd/bar/some.txt"))
        self.assertTrue(dpf("/abc/bar/some.txt"))
        self.assertTrue(dpf("/foo/bar/abc/some.txt"))
        #
        self.assertFalse(dpf("/foo/bar/baz/abc.txt"))

        dpf = directory_pattern_predicate("^/abc")
        self.assertTrue(dpf("/abc/bar/some.txt"))
        #
        self.assertFalse(dpf("abc/bar/some.txt"))

        dpf = directory_pattern_predicate("abc$")
        self.assertTrue(dpf("foo/bar/abc/some.txt"))
        #
        self.assertFalse(dpf("abc/abc/bar/some.txt"))
        self.assertFalse(dpf("abc/abc/bar/abc.abc"))

    def test_last_modified_filter(self):
        file_name = os.path.realpath(__file__)

        lmaf = last_modified_after_predicate()
        self.assertTrue(lmaf(file_name))

        lmaf = last_modified_after_predicate(3000000000)
        # valid until 2065-01-24 06:20:00
        self.assertFalse(lmaf(file_name))



