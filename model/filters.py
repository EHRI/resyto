#! /usr/bin/env python3
# -*- coding: utf-8 -*-
import os, logging
import re
from abc import ABCMeta, abstractmethod

logger = logging.getLogger(__name__)


class Filters(object):

    def __init__(self):
        self.including_filters=[]
        self.excluding_filters=[]

    def including(self, *including):
        for filter in including:
            if isinstance(filter, Filter):
                self.including_filters.append(filter)
        return self

    def excluding(self, *excluding):
        for filter in excluding:
            if isinstance(filter, Filter):
                self.excluding_filters.append(filter)
        return self

    def remove(self, filter):
        if filter in self.including_filters:
            self.including_filters.remove(filter)
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
                logger.debug("%s includes %s", filter.__class__.__name__, name)
                break
        if _accept:
            for filter in self.excluding_filters:
                if filter.passes(name, **kwargs):
                    _accept = False
                    logger.debug("%s excludes %s", filter.__class__.__name__, name)
                    break

        return _accept


class Filter(object, metaclass=ABCMeta):
    """
    Permitting filter when including; restricting filter when excluding.
    """

    @abstractmethod
    def passes(self, name, **kwargs):
        raise NotImplementedError()


class And(Filter):
    """
    Conjunction relation for filters.
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
