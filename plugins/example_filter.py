"""
This is an example of subclassing model.filters.Filter and exposing the subclasses as plugins
through the util.plugger module.
"""

#! /usr/bin/env python3
# -*- coding: utf-8 -*-

from util.filters import Filter


class XPathFilter(Filter):
    """
    Filters xml files that contain a given xpath expression.
    """
    # def __init__(self, expression, foo=True, bar=False):
    #     self.expression = expression

    expression = "bla"

    def passes(self, name, **kwargs):
        print(self.__class__.__name__, self.expression, name, kwargs)
        return True

    def do_something(self, foo, bar):
        pass


class SourceXpathFilter(XPathFilter):

    expression = "source='bor'"
    def __init__(self):
        pass


class NameFilter(Filter):

    def passes(self, name, **kwargs):
        print(self.__class__.__name__, name, kwargs)


class NotAFilter():
    pass