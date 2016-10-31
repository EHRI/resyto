#! /usr/bin/env python3
# -*- coding: utf-8 -*-
from model.executors import Executor


class NewChangelistExecutor(Executor):

    def generate_rs_documents(self, filenames: iter):
        pass


class IncrementalChangelistExecutor(Executor):

    def generate_rs_documents(self, filenames: iter):
        pass