#! /usr/bin/env python3
# -*- coding: utf-8 -*-
import unittest

from model.strategy import Strategy


class Test_Strategy(unittest.TestCase):

    def test_ordinal(self):
        strategy = Strategy.resourcelist
        print(Strategy(1))

        print(Strategy(1).value)

        print(strategy)

        print(Strategy['resourcelist'])

        value = "changelist"
        Strategy[value]

        # value = "foo"
        # Strategy[value]

        print (list(Strategy))
        print(Strategy.names())

        print(type(strategy.name))
        print(strategy.name)
        self.assertEqual(strategy, Strategy(0))


