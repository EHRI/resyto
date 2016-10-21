#! /usr/bin/env python3
# -*- coding: utf-8 -*-
import unittest

from util import filters
from util.filters import Filters, And, FilenamePatternFilter, DirectoryPatternFilter, HiddenFileFilter, Not, Filter


def passes(self, name, **kwargs):
    pass


class TestFilter(unittest.TestCase):

    def test_listFilters(self):
        filter_classes = filters.list_filter_subclasses()
        self.assertIsInstance(filter_classes, list)
        #for filter in filter_classes:
        #    print(filter.__name__)

    def test_is_filter_duck_type(self):
        self.assertTrue(filters.is_filter_duck_type(Filter))
        self.assertTrue(filters.is_filter_duck_type(Filter()))
        self.assertTrue(filters.is_filter_duck_type(And))
        self.assertTrue(filters.is_filter_duck_type(And()))
        self.assertTrue(filters.is_filter_duck_type(TestFilter))
        self.assertTrue(filters.is_filter_duck_type(TestFilter()))

        self.assertFalse(filters.is_filter_duck_type(TestFilenamePatternFilter))
        self.assertFalse(filters.is_filter_duck_type(TestFilenamePatternFilter()))

        # don't know how to call functions on modules
        # module = inspect.getmodule(self)
        # self.assertTrue(filters.is_filter_duck_type(module))

    def passes(self, name, **kwargs):
        pass


class TestFilenamePatternFilter(unittest.TestCase):

    def test_passes(self):
        filter = FilenamePatternFilter("abc")
        self.assertTrue(filter.passes("foo/bar/abc"))
        self.assertTrue(filter.passes("foo/bar/abc.txt"))
        self.assertTrue(filter.passes("foo/bar/defabc.txt"))

        filter = FilenamePatternFilter("^abc")
        self.assertTrue(filter.passes("foo/bar/abc"))
        self.assertTrue(filter.passes("foo/bar/abc.txt"))
        self.assertFalse(filter.passes("foo/bar/defabc.txt"))

        filter = FilenamePatternFilter(".txt$")
        self.assertFalse(filter.passes("foo/bar/abc"))
        self.assertTrue(filter.passes("foo/bar/abc.txt"))
        self.assertFalse(filter.passes("foo/bar/def.txt.abc"))


class TestAnd(unittest.TestCase):

    def test_empty_filter(self):
        filter = And()
        self.assertFalse(filter.passes(""))
        self.assertFalse(filter.passes(None))

    def test_passes(self):
        filter = And(
            DirectoryPatternFilter("^foo/bar"),
            FilenamePatternFilter(".txt$")
        )
        self.assertTrue(filter.passes("foo/bar/abc.txt"))
        self.assertFalse(filter.passes("foo/bas/abc.txt"))
        self.assertFalse(filter.passes("foo/bar/abc.xml"))


class TestFilters(unittest.TestCase):

    def test_empty(self):
        filters = Filters()
        self.assertFalse(filters.accept(""))
        self.assertFalse(filters.accept(None))

    def test_add_includes_with_None(self):
        filters = Filters()
        filters.add_including(None)
        self.assertEquals(0, len(filters.including_filters))

    def test_add_includes_with_type(self):
        filters = Filters()
        filters.add_including(Filter.__class__)
        filters.add_including(Filter().__class__)

        self.assertEquals(0, len(filters.including_filters))
        self.assertFalse(filters.accept("anything"))

        filters.add_including(Filter())
        self.assertEquals(1, len(filters.including_filters))
        self.assertTrue(filters.accept("anything"))

    def test_accept_folder_and_file(self):
        filters = Filters()
        filters.add_including(
            And(
                DirectoryPatternFilter("^foo/bar"),
                FilenamePatternFilter(".txt$")
            )
        )
        filters.add_excluding(
            HiddenFileFilter()
        )

        self.assertTrue(filters.accept("foo/bar/abc.txt"))
        self.assertTrue(filters.accept("foo/bar/hide.txt"))

        self.assertFalse(filters.accept("foo/bas/abc.txt"))
        self.assertFalse(filters.accept("foo/bar/abc.xml"))
        self.assertFalse(filters.accept("foo/bar/.hide.txt"))

    def test_accept_folders_and_not_file_extension_in_some_folder(self):
        filters = Filters()
        filters.add_including(
            And(
                DirectoryPatternFilter("^foo/bar"),
                Not(FilenamePatternFilter(".txt$"))
            ),
            DirectoryPatternFilter("^bor/tor")

        )
        filters.add_excluding(
            HiddenFileFilter()
        )

        self.assertFalse(filters.accept("foo/bar/abc.txt"))
        self.assertFalse(filters.accept("foo/bar/hide.txt"))
        self.assertFalse(filters.accept("foo/bas/abc.xml"))
        self.assertFalse(filters.accept("foo/bar/.hide.txt"))

        self.assertTrue(filters.accept("foo/bar/abc.xml"))
        self.assertTrue(filters.accept("foo/bar/abc.doc"))

        self.assertTrue(filters.accept("bor/tor/abc.txt"))
        self.assertTrue(filters.accept("bor/tor/abc.xml"))
        self.assertFalse(filters.accept("bor/tor/.abc.txt"))




