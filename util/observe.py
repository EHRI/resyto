#! /usr/bin/env python3
# -*- coding: utf-8 -*-
import logging
from abc import ABCMeta, abstractmethod


class Observable(object):
    def __init__(self):
        self.observers = []

    def register(self, observer):
        if not observer in self.observers:
            self.observers.append(observer)

    def unregister(self, observer):
        if observer in self.observers:
            self.observers.remove(observer)

    def unregister_all(self):
        if self.observers:
            del self.observers[:]

    def update_observers(self, *args, **kwargs):
        for observer in self.observers:
            observer.update(*args, **kwargs)


class Observer(object):
    __metaclass__ = ABCMeta

    @abstractmethod
    def update(self, *args, **kwargs):
        pass


class EventPrinter(Observer):

    def __init__(self, event_level = 0):
        self.event_level = event_level

    def update(self, *args, **kwargs):
        if len(args) == 2:
            try:
                source = args[0].__class__.__name__
                event = args[1]
                if event.value >= self.event_level:
                    print(source, event.name, kwargs)
            except AttributeError:
                print("unexpected args: ", args)
        else:
            print(args, kwargs)


class EventLogger(Observer):

    def __init__(self, logging_level=logging.DEBUG, event_level=0):
        self.logger = logging.getLogger(__name__)
        self.logging_level = logging_level
        self.event_level = event_level

    def update(self, *args, **kwargs):
        if len(args) == 2:
            try:
                source = args[0].__class__.__name__
                event = args[1]
                if event.value >= self.event_level:
                    self.logger.log(self.logging_level, "%s, %s, %s" % (source, event.name, kwargs))
            except AttributeError:
                self.logger.warn("unexpected args: " % args)
        else:
            self.logger.log(self.logging_level, "%s, %s" % (args, kwargs))


class SelectiveEventPrinter(Observer):

    def __init__(self, *events):
        self.events = events

    def update(self, *args, **kwargs):
        if len(args) > 1:
            event = args[1]
            if not self.events is None:
                if event in self.events:
                    try:
                        source = args[0].__class__.__name__
                        print(source, event.name, kwargs)
                    except AttributeError:
                        print("unexpected args: %s", args)


class SelectiveEventLogger(Observer):

    def __init__(self, *events, level=logging.DEBUG):
        self.events = events
        self.logger = logging.getLogger(__name__)
        self.level = level

    def update(self, *args, **kwargs):
        if len(args) > 1:
            event = args[1]
            if not self.events is None:
                if event in self.events:
                    try:
                        source = args[0].__class__.__name__
                        self.logger.log(self.level, "%s, %s, %s" % (source, event.name, kwargs))
                    except AttributeError:
                        self.logger.warn("unexpected args: %s" % args)