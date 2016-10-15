#! /usr/bin/env python3
# -*- coding: utf-8 -*-
import unittest

from model.strategy import Strategy


class Test_Strategy(unittest.TestCase):

    def test_names(self):
        names = Strategy.names()
        self.assertIsInstance(names, list)
        self.assertEqual(names, ['changedump', 'changelist', 'resourcedump', 'resourcelist'])

    def test_ordinal(self):
        # get the int value of an enum
        self.assertEqual(Strategy.resourcelist.value, 0)

    def test_conversion(self):
        # get an enum by name
        self.assertIs(Strategy['resourcelist'], Strategy.resourcelist)
        # get a enum by value
        self.assertIs(Strategy(0), Strategy.resourcelist)
        self.assertIs(Strategy(1), Strategy.changelist)
        self.assertIs(Strategy(2), Strategy.resourcedump)
        self.assertIs(Strategy(3), Strategy.changedump)



