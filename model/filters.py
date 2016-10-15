#! /usr/bin/env python3
# -*- coding: utf-8 -*-
import os, logging


logger = logging.getLogger(__name__)


class FileLocationException(Exception):
    pass


class FileFilters(object):

    def __init__(self, filters=list):
        self.filters=[]
        for filter in filters:
            self.add(filter)

    def add(self, file_filter):
        assert(isinstance(file_filter, FileFilter))
        self.filters.append(file_filter)

    def remove(self, file_filter):
        if file_filter in self.filters:
            self.filters.remove(file_filter)

    def accept(self, filename, **kwargs):
        _accept = False
        for file_filter in self.filters:
            if file_filter.includes(filename, **kwargs):
                _accept = True
                break
        if _accept:
            for file_filter in self.filters:
                if file_filter.excludes(filename, **kwargs):
                    _accept = False
                    break

        if not _accept:
            logger.debug("Excluding %s", filename)
        return _accept


class FileFilter(object):
    """
    Permissive FileFilter.
    """

    def includes(self, filename, **kwargs):
        return True

    def excludes(self, filename, **kwargs):
        return False


class SimpleFileFilter(FileFilter):

    def __init__(self, included=list(), excluded=list()):
        self.included = included
        self.excluded = excluded

    def includes(self, filename, **kwargs):
        return filename in self.included

    def excludes(self, filename, **kwargs):
        return filename in self.excluded


class ExcludeHiddenFileFilter(FileFilter):

    def excludes(self, filename, **kwargs):
        return os.path.basename(filename).startswith(".")


class IncludeDirectoryFileFilter(FileFilter):

    def __init__(self, basepath, stop_on_error=False):
        self.basepath = basepath
        self.stop_on_error = stop_on_error

    def includes(self, filename, **kwargs):
        _accept = True
        if not filename.startswith(self.basepath):
            _accept = False
            if self.stop_on_error:
                raise FileLocationException("Not on basepath. $s <> $s", filename, self.basepath)
        return _accept


class ExcludeDirectoryFileFilter(FileFilter):

    def __init__(self, dir_path):
        self.dir_path = dir_path

    def excludes(self, filename, **kwargs):
        return filename.startswith(self.dir_path)
