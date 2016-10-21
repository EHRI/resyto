#! /usr/bin/env python3
# -*- coding: utf-8 -*-
import unittest

from util import defaults


class TestDefaults(unittest.TestCase):

    def test_sanitize_url(self):
        self.assertEquals("", defaults.sanitize_url_prefix(None))
        self.assertEquals("http://foo.com/path/", defaults.sanitize_url_prefix("http://foo.com/path"))
        self.assertEquals("http://foo.com/path;parameter/", defaults.sanitize_url_prefix("http://foo.com/path;parameter"))

        with self.assertRaises(Exception) as context:
            defaults.sanitize_url_prefix("http://foo.com/path?this=that")
        self.assertIsInstance(context.exception, ValueError)

    def test_w3c_datetime(self):
        self.assertEquals("2016-10-15T14:08:31Z", defaults.w3c_datetime(1476540511))



