#! /usr/bin/env python3
# -*- coding: utf-8 -*-

import unittest

from model.filters import Filters,  And, FilenamePatternFilter, DirectoryPatternFilter, HiddenFileFilter, Not


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

    def test_accept_folder_and_file(self):
        filters = Filters()
        filters.including(
            And(
                DirectoryPatternFilter("^foo/bar"),
                FilenamePatternFilter(".txt$")
            )
        ).excluding(
            HiddenFileFilter()
        )

        self.assertTrue(filters.accept("foo/bar/abc.txt"))
        self.assertTrue(filters.accept("foo/bar/hide.txt"))

        self.assertFalse(filters.accept("foo/bas/abc.txt"))
        self.assertFalse(filters.accept("foo/bar/abc.xml"))
        self.assertFalse(filters.accept("foo/bar/.hide.txt"))

    def test_accept_folders_and_not_file_extension_in_some_folder(self):
        filters = Filters()
        filters.including(
            And(
                DirectoryPatternFilter("^foo/bar"),
                Not(FilenamePatternFilter(".txt$"))
            ),
            DirectoryPatternFilter("^bor/tor")

        ).excluding(
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




