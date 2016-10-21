#! /usr/bin/env python3
# -*- coding: utf-8 -*-
import inspect
import logging
import os
import re
from abc import ABCMeta, abstractmethod

from util import plugger

LOG = logging.getLogger(__name__)


class Filter(object):
    """
    All permissive filter.
    """
    def passes(self, name, **kwargs):
        """
        Core function of a Filter: let something pass or not pass.
        :param name: a named argument
        :param kwargs: optional key-value arguments
        :return: True if this filter passes, False if not.
        """
        return True


def list_filter_subclasses():
    """
    List the loaded subclasses of Filter.
    :return:
    """
    return Filter.__subclasses__()


def is_filter_duck_type(filter):
    """
    Inspects if the given class or object has the function 'passes(self, name, **kwargs)'.
    :param filter: the class or object to be inspected
    :return: True if it can be duck-type-used as Filter, False otherwise.
    """
    duck_type = isinstance(filter, Filter)
    if not duck_type and plugger.has_function(filter, "passes"):
        argspec = inspect.getargspec(filter.passes)
        if len(argspec.args) == 2 and argspec.varargs is None and argspec.keywords:
            duck_type = True
    if not duck_type:
        LOG.warn("Not a filter duck type: %s %s" % (filter.__class__.__name__, filter))
    return duck_type


class Filters(object):
    """
    A collection of filters separated in two groups, including filters and excluding filters. The logical relation
    between filters in a group is subjunctive (or). The excluding group is negated (not). The boolean return
    value of the 'accept' function can be written as

        accept = (incl_1 or incl_2 or ... or incl_n) and not(excl_1 or excl_2 or ... or excl_n)

    where incl_1 ... incl_n are filters from the including group and excl_1 ... excl_n are filters from the
    excluding group. If there are no filters in the including group the result is always False.

    See for grouping filters in an 'and' relation the class util.filters.And.
    See for negating filters the class util.filters.Not.
    """
    def __init__(self):
        self.including_filters=[]
        self.excluding_filters=[]

    def add_including(self, *including):
        """
        Save addition of including filters.
        """
        for filter in including:
            if is_filter_duck_type(filter):
                if isinstance(filter, type):
                    LOG.warn("Not a filter duck: %s", filter)
                else:
                    self.including_filters.append(filter)

    def add_excluding(self, *excluding):
        """
        Save addition of excluding filters
        """
        for filter in excluding:
            if is_filter_duck_type(filter):
                if isinstance(filter, type):
                    LOG.warn("Not a filter duck: %s", filter)
                else:
                    self.excluding_filters.append(filter)

    def remove_from_includes(self, filter):
        """
        Save removal from including_filters.
        """
        if filter in self.including_filters:
            self.including_filters.remove(filter)

    def remove_from_excludes(self, filter):
        """
        Save removal from excluding filters.
        """
        if filter in self.excluding_filters:
            self.excluding_filters.remove(filter)

    def accept(self, name, **kwargs):
        """
        accept = (incl_1 or incl_2 or ... or incl_n) and not(excl_1 or excl_2 or ... or excl_n)
        """
        _accept = False
        for filter in self.including_filters:
            if filter.passes(name, **kwargs):
                _accept = True
                LOG.debug("%s includes %s", filter.__class__.__name__, name)
                break
        if _accept:
            for filter in self.excluding_filters:
                if filter.passes(name, **kwargs):
                    _accept = False
                    LOG.debug("%s excludes %s", filter.__class__.__name__, name)
                    break

        return _accept


class FilterBuilder(metaclass=ABCMeta):
    """
    Subclasses of this abstract class may be searched and called to contribute to, remove from -or replace-
    the set of filters collected in a Filters object.
    Searching of FilterBuilders for a particular task may be made possible by a convention in naming.
    """
    @abstractmethod
    def build_filters(self, filters, *kwargs):
        """
        Contribute to, remove from -or replace- the set of filters collected in the Filters object.
        :param filters: a Filters object
        :param kwargs: optional key-value arguments
        :return: a Filters object
        """
        return filters


class And(Filter):
    """
    Logical conjunction of filters.
    """
    def __init__(self, *filters):
        self.filters = []
        for filter in filters:
            if isinstance(filter, Filter):
                self.filters.append(filter)

    def passes(self, name, **kwargs):
        """
        passes = filter_1.passes and filter_2.passes and ... and filter_n.passes
        """
        passes = len(self.filters) > 0
        for filter in self.filters:
            if not filter.passes(name, **kwargs):
                passes = False
                break
        return passes


class Not(Filter):
    """
    Negating filter.
    """
    def __init__(self, filter):
        assert isinstance(filter, Filter)
        self.filter = filter

    def passes(self, name, **kwargs):
        return not self.filter.passes(name, **kwargs)


class NameFilter(Filter):

    def __init__(self, *items):
        self.item_list = list(items)

    def passes(self, name, **kwargs):
        return name in self.item_list


class HiddenFileFilter(Filter):

    def passes(self, file_path, **kwargs):
        # in Python 3.5 this should work
        # return bool(os.stat(file_path).st_file_attributes & os.stat.FILE_ATTRIBUTE_HIDDEN)
        return os.path.basename(file_path).startswith(".")


class DirectoryPatternFilter(Filter):

    def __init__(self, name_pattern):
        self.pattern = re.compile(name_pattern)

    def passes(self, file_path, **kwargs):
        return self.pattern.search(os.path.dirname(file_path))


class FilenamePatternFilter(Filter):

    def __init__(self, name_pattern):
        self.pattern = re.compile(name_pattern)

    def passes(self, file_path, **kwargs):
        return self.pattern.search(os.path.basename(file_path))
