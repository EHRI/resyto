#! /usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import unittest

import time

import util.plugger as plg
from util.filters import Filter


class TestPlugger(unittest.TestCase):

    def test_list_py_files(self):
        user_home = os.path.expanduser("~")
        for py_file in plg.Plugger.list_py_files("plugins", os.path.join(user_home, "tmp")):
            print(py_file)

    def test_load_modules(self):
        plugger = plg.Plugger(stop_on_error=False)
        user_home = os.path.expanduser("~")
        for module in plugger.load_modules("plugins", os.path.join(user_home, "tmp")):
            print(module)

    def test_list_classes(self):
        plugger = plg.Plugger(stop_on_error=False)
        user_home = os.path.expanduser("~")
        for cls in plugger.list_classes("plugins", os.path.join(user_home, "tmp")):
            print(cls)

    def test_list_classes_filtered(self):
        plugger = plg.Plugger(stop_on_error=False)
        fs = [lambda cls: plg.is_named("NameFilter"),
                   plg.from_module("py_test.filters")]
        directories = ["plugins", os.path.join(os.path.expanduser("~"), "tmp")]
        for cls in plugger.list_classes_filtered(fs, *directories):
            print(cls)

        print ("===================no filter")
        for cls in plugger.list_classes_filtered(None, *directories):
            print(cls)

    def test_list_classes_filtered2(self):
        plugger = plg.Plugger(stop_on_error=False)
        is_named = lambda cls: cls.__name__ == "NameFilter"
        from_module = lambda cls: cls.__module__.startswith("py_test")

        fs = [_nor_(is_named, from_module)

              ]

        directories = ["plugins", os.path.join(os.path.expanduser("~"), "tmp")]

        for clazz in plugger.list_classes_filtered(fs, *directories):
            print(clazz)


def _not_(predicate):
    __not__ = lambda cls : not predicate(cls)
    return __not__


def _or_(*predicates):
    __or__ = lambda cls : [cls for predicate in predicates if predicate(cls)]
    return __or__


def _nor_(*predicates):
    return _not_(_or_(*predicates))



    # def test_has_function(self):
    #     self.assertTrue(util.plugger.has_function(Filter, "passes"))
    #     self.assertTrue(util.plugger.has_function(Filter(), "passes"))
    #     self.assertFalse(util.plugger.has_function(Filter, "strange_name"))
    #     self.assertFalse(util.plugger.has_function(Filter(), "strange_name"))
    #
    #     self.assertTrue(util.plugger.has_function(TestPlugger, "strange_name"))
    #     self.assertTrue(util.plugger.has_function(TestPlugger(), "strange_name"))
    #     self.assertFalse(util.plugger.has_function(TestPlugger, "passes"))
    #     self.assertFalse(util.plugger.has_function(TestPlugger(), "passes"))
    #
    # def strange_name(self):
    #     pass






    # def test_load(self):
    #     for cls in plugger.list_subclasses(Filter, "plugins"):
    #         print("==============================")
    #         print(cls)
    #         print(inspect.getdoc(cls))
    #         print(inspect.getargspec(cls.__init__))
    #
    #         init_args = inspect.getargspec(cls.__init__)
    #         print (len(init_args.args) == 1)
    #
    #         filter = cls.__new__(cls)
    #         print(filter)
    #
    #         print(filter.passes("foo"))




