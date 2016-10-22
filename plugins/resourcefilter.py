#! /usr/bin/env python3
# -*- coding: utf-8 -*-
import inspect
import logging
import os
import re
from abc import ABCMeta, abstractmethod

from util.gates import or_, and_, gate, is_one_arg_predicate, GateCreationException
from util.plugg import Inspector, has_function

LOG = logging.getLogger(__name__)


class ResourceGateBuilder(metaclass=ABCMeta):
    @abstractmethod
    def build_includes(self, includes: list) -> list:
        return includes

    @abstractmethod
    def build_excludes(self, excludes: list) -> list:
        return excludes


class DefaultResourceGateBuilder(ResourceGateBuilder):
    def __init__(self, *plugin_directories):
        self.plugin_directories = plugin_directories
        self.includes = []
        self.excludes = []

    def build_includes(self, includes=list()):

        self.includes.extend(includes)
        return self.includes

    def build_excludes(self, excludes=list()):
        self.excludes.extend(excludes)
        return self.excludes

    def build(self):
        inspector = Inspector(stop_on_error=True)
        # search for builders that either have ResourceGateBuilder as superclass
        # or have both methods build_includes and build_excludes.
        is_subclass = lambda x: issubclass(x, ResourceGateBuilder)
        has_both_metods = and_(has_function("build_includes"), has_function("build_excludes"))
        predicates = [or_(is_subclass, has_both_metods)]

        for cls in inspector.list_classes_filtered(predicates, *self.plugin_directories):

            if inspect.isabstract(cls):
                LOG.warn("ResourceGateBuilder cannot be instantiated: class is abstract: %s" % cls)
            else:
                try:
                    builder = cls.__new__(cls)
                    builder.__init__()
                except TypeError as exc:
                    raise ResourceGateBuilderException("Could not instantiate object (%s in %s)"
                                                       % (cls, inspect.getfile(cls))) from exc

                tmp_includes = builder.build_includes(list(self.includes))
                if not isinstance(tmp_includes, list):
                    raise ResourceGateBuilderException("Illegal return value for build_includes: "
                                                       "%s in stead of list. (%s in %s)" % (
                                                       self.includes, cls, inspect.getfile(cls)))
                tmp_excludes = builder.build_excludes(list(self.excludes))
                if not isinstance(tmp_excludes, list):
                    raise ResourceGateBuilderException("Illegal return value for build_excludes: "
                                                       "%s in stead of list. (%s in %s)" % (
                                                       self.excludes, cls, inspect.getfile(cls)))

                self._inspect_predicates(tmp_includes, tmp_excludes, cls)

                new_in_incl = len([x for x in tmp_includes if x not in self.includes])
                out_of_incl = len([x for x in self.includes if x not in tmp_includes])
                new_in_excl = len([x for x in tmp_excludes if x not in self.excludes])
                out_of_excl = len([x for x in self.excludes if x not in tmp_excludes])
                self.includes = tmp_includes
                self.excludes = tmp_excludes
                LOG.info("Includes build by %s. new: %d, removed: %d" % (cls, new_in_incl, out_of_incl))
                LOG.info("Excludes build by %s. new: %d, removed: %d" % (cls, new_in_excl, out_of_excl))

        return gate(self.includes, self.excludes)

    @staticmethod
    def _inspect_predicates(includes, excludes, cls):
        try:
            valid = [p for p in includes if is_one_arg_predicate(p)]
        except GateCreationException as exc:
            raise ResourceGateBuilderException("Invalid include predicate from %s" % cls) from exc

        try:
            valid = [p for p in excludes if is_one_arg_predicate(p)]
        except GateCreationException as exc:
            raise ResourceGateBuilderException("Invalid exclude predicate from %s" % cls) from exc


class ResourceGateBuilderException(RuntimeError):
    pass


def hidden_file_predicate():
    # in Python 3.5 this should work
    # return lambda file_path : bool(os.stat(file_path).st_file_attributes & os.stat.FILE_ATTRIBUTE_HIDDEN)
    return lambda file_path: isinstance(file_path, str) and os.path.basename(file_path).startswith(".")


def directory_pattern_predicate(name_pattern=""):
    pattern = re.compile(name_pattern)
    return lambda file_path: isinstance(file_path, str) and pattern.search(os.path.dirname(file_path))


def filename_pattern_predicate(name_pattern=""):
    pattern = re.compile(name_pattern)
    return lambda file_path: isinstance(file_path, str) and pattern.search(os.path.basename(file_path))


def last_modified_after_predicate(t=0):
    def _file_attribute_filter(file_path):
        if not os.path.exists(file_path):
            return False
        else:
            lm = os.stat(file_path).st_mtime
            return lm > t

    return _file_attribute_filter
