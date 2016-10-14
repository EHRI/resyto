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
        list = dir(Strategy)
        del list[0:4]
        return list


