#! /usr/bin/env python3
# -*- coding: utf-8 -*-


import logging, logging.config, sys
import i18n

from PyQt5.QtWidgets import QApplication
from control.rs_window import RsMainWindow
from model.config import Configuration

logging.config.fileConfig('logging.conf')

logger = logging.getLogger(__name__)


class RsApplication(QApplication):

    def __init__(self, args):
        super().__init__(args)

        logger.info("Starting application")

        language = Configuration().settings_language()
        i18n.set_language(language)

        self.main_window = RsMainWindow()

        self.aboutToQuit.connect(self.__before_close__)

        sys.exit(self.exec_())

    def __before_close__(self):
        # any final action?
        logger.info("Closing application")
        self.main_window.close()


if __name__ == '__main__':
    app = RsApplication(sys.argv)
    #sys.exit(app.exec_())