#! /usr/bin/env python3
# -*- coding: utf-8 -*-
from PyQt5.QtWidgets import QMainWindow, QAction, qApp, QTabWidget, QWidget

from view.config_frame import ConfigFrame
from view.upload_frame import UploadFrame


class RsMainWindow(QMainWindow):

    def __init__(self):
        super().__init__()
        self.menubar = self.menuBar()
        self.create_menu()

        self.tabframe = TabbedFrame(self)
        self.setCentralWidget(self.tabframe)
        self.resize(780, 380)
        self.show()

    def show_configure(self):
        self.tabframe.setCurrentIndex(0)

    def show_upload(self):
        self.tabframe.setCurrentIndex(1)

    def create_menu(self):

        exit_action = QAction(_("&Exit"), self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.setStatusTip(_("Exit application"))
        exit_action.triggered.connect(qApp.quit)

        show_configure_action = QAction(_("&Configure"), self)
        show_configure_action.setShortcut("Ctrl+C")
        show_configure_action.setStatusTip(_("Configure rsync"))
        show_configure_action.triggered.connect(self.show_configure)

        show_upload_action = QAction(_("&Upload"), self)
        show_upload_action.setShortcut("Ctrl+U")
        show_upload_action.setStatusTip(_("Upload files"))
        show_upload_action.triggered.connect(self.show_upload)

        some_action = QAction("&Something", self)

        show_main_action = QAction("&Main window", self)

        self.menubar.setNativeMenuBar(True)

        file_menu = self.menubar.addMenu(_("&File"))
        file_menu.addAction(some_action)
        file_menu.addAction(exit_action)             # on mac under [application] > Quit [application]

        view_menu = self.menubar.addMenu(_("&View"))
        view_menu.addAction(show_main_action)
        view_menu.addAction(show_configure_action)   # on mac under [application] > Preferences
        view_menu.addAction(show_upload_action)


class TabbedFrame(QTabWidget):

    def __init__(self, parent):
        super().__init__(parent)
        self.currentChanged.connect(self.__tabchanged)
        self.previndex = -1
        self.configframe = ConfigFrame(self)
        self.uploadframe = UploadFrame(self)
        self.init_ui()

    def __tabchanged(self, index):
        print(index)
        if self.previndex > -1:
            self.widget(self.previndex).hide()
        self.previndex = index

    def init_ui(self):
        self.addTab(self.configframe, _("&Configuration"))

        self.addTab(self.uploadframe, _("Upload"))

        self.addTab(QWidget(), _("Statistics"))
        self.addTab(QWidget(), _("Manual Sets"))
        self.addTab(QWidget(), _("Rule-based Sets"))

