#! /usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import i18n

from PyQt5.QtWidgets import QApplication

from control.rs_window import RsMainWindow
from model.config import Configuration


class RsApplication(QApplication):

    def __init__(self, args):
        super().__init__(args)
        language = Configuration().settings_language()
        i18n.set_language(language)

        main_window = RsMainWindow()

        print("starting")
        self.aboutToQuit.connect(self.__before_close__)

        sys.exit(self.exec_())

    def __before_close__(self):
        # any final action?
        print("closing")


if __name__ == '__main__':
    app = RsApplication(sys.argv)
    #sys.exit(app.exec_())