#! /usr/bin/env python3
# -*- coding: utf-8 -*-

import unittest
import i18n

class Testi18n(unittest.TestCase):

    def test_01_get_languages(self):
        languages = i18n.get_languages()
        print(languages)
        assert len(languages) > 1


