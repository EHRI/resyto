#! /usr/bin/env python3
# -*- coding: utf-8 -*-

from enum import Enum, unique


@unique
class Strategy(Enum):
    resourcelist = 0
    changelist = 1
    resourcedump = 2
    changedump = 3

    @staticmethod
    def names():
        """
        Get the names of this Enum, whithout other method names.
        :return: List<str> of names
        """
        names = dir(Strategy)
        # = ['__class__', '__doc__', '__members__', '__module__', 'changedump', 'changelist', 'resourcedump', 'resourcelist']
        del names[0:4]
        return names # ['changedump', 'changelist', 'resourcedump', 'resourcelist']

    @staticmethod
    def sanitize(name):
        try:
            strategy = Strategy[name]
            return strategy.name
        except KeyError as err:
            raise ValueError(err)

