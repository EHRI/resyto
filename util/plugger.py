#! /usr/bin/env python3
# -*- coding: utf-8 -*-
import importlib
import inspect
import logging
import os, sys


APPLICATION_HOME = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))

LOG = logging.getLogger(__name__)



class Plugger(object):

    def __init__(self, stop_on_error=False):
         self.stop_on_error = stop_on_error

    @staticmethod
    def list_py_files(*directories):
        for dir in directories:
            abs_dir = os.path.join(APPLICATION_HOME, dir)
            for root, _directories, _filenames in os.walk(abs_dir):
                for filename in _filenames:
                    if filename.endswith(".py") and not filename.startswith("__init__"):
                        py_file = os.path.join(root, filename)
                        yield py_file

    def load_modules(self, *directories):
        for dir in directories:
            abs_dir = os.path.join(APPLICATION_HOME, dir)
            plugin_home = APPLICATION_HOME
            if not abs_dir.startswith(APPLICATION_HOME):
                plugin_home = abs_dir
                sys.path.append(plugin_home)

            for py_file in self.list_py_files(abs_dir):
                names = py_file.rsplit(".", 1) # everything but the extension
                path = os.path.relpath(names[0], plugin_home).replace(os.sep, ".")
                try:
                    module = importlib.import_module(path)
                    yield module
                except ImportError as ex:
                    if self.stop_on_error:
                        raise ex
                    else:
                        LOG.exception(ex)

    def list_classes(self, *directories):
        for module in self.load_modules(*directories):
            clsmembers = inspect.getmembers(module, inspect.isclass)
            for cls in clsmembers:
                if cls[1].__module__ == module.__name__:
                    yield cls[1]

    def list_classes_filtered(self, filters=list(), *directories):
        for cls in self.list_classes(*directories):
            passes = True
            if (filters):
                for f in filters:
                    if not f(cls):
                        passes = False
                        break
            if passes:
                yield cls
        # another implementation, not exploiting yield:
        # classes = self.list_classes(*directories)
        # if filters:
        #     for f in filters:
        #         classes = filter(f, classes)
        # return classes


## Closures for class filtering
def is_subclass_of(super):
    def _is_subclass_of(cls): return issubclass(cls, super)
    return _is_subclass_of


def is_qnamed(qname):
    def _is_qnamed(cls): return qname == cls.__module__ + "." + cls.__name__
    return _is_qnamed


def is_named(name):
    def _is_named(cls): return name == cls.__name__ or name == cls.__module__ + "." + cls.__name__
    return _is_named


def from_module(module_name):
    def _from_module(cls): return cls.__module__ == module_name
    return _from_module


def has_function(function_name):
    def _has_function(cls):
        if isinstance(cls, type):
            clazz = cls
        else:
            clazz = cls.__class__

        func_descs = inspect.getmembers(clazz, inspect.isfunction)
        for func_desc in func_descs:
            if func_desc[0] == function_name:
                return True
        return False
    return _has_function


def _not_(predicate):
    __not__ = lambda x: not predicate(x)
    return __not__


def _or_(*predicates):
    __or__ = lambda x: [x for predicate in predicates if predicate(x)]
    return __or__


def _nor_(*predicates):
    return _not_(_or_(*predicates))




