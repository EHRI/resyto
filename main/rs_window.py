#! /usr/bin/env python3
# -*- coding: utf-8 -*-
from PyQt5.QtWidgets import QMainWindow, QAction, qApp, QTabWidget, QWidget

from views.config_frame import ConfigFrame
from views.upload_frame import UploadFrame


class RsMainWindow(QMainWindow):

    def __init__(self):
        super().__init__()
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

        exit_action = QAction("&Exit", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.setStatusTip("Exit application")
        exit_action.triggered.connect(qApp.quit)

        show_configure_action = QAction("&Configure", self)
        show_configure_action.setShortcut("Ctrl+C")
        show_configure_action.setStatusTip("Configure rsync")
        show_configure_action.triggered.connect(self.show_configure)

        show_upload_action = QAction("&Upload", self)
        show_upload_action.setShortcut("Ctrl+U")
        show_upload_action.setStatusTip("Uploafd files")
        show_upload_action.triggered.connect(self.show_upload)


        some_action = QAction("&Something", self)

        showMainAction = QAction("&Main window", self)

        self.menubar = self.menuBar()
        self.menubar.setNativeMenuBar(True)

        fileMenu = self.menubar.addMenu("&File")
        fileMenu.addAction(some_action)
        fileMenu.addAction(exit_action)             # on mac under [application] > Quit [application]

        viewMenu = self.menubar.addMenu("&View")
        viewMenu.addAction(showMainAction)
        viewMenu.addAction(show_configure_action)   # on mac under [application] > Preverences
        viewMenu.addAction(show_upload_action)


class TabbedFrame(QTabWidget):

    def __init__(self, parent):
        super().__init__(parent)
        self.currentChanged.connect(self.__tabchanged)
        self.previndex = -1
        self.initUI()

    def __tabchanged(self, index):
        print(index)
        if self.previndex > -1:
            self.widget(self.previndex).hide()
        self.previndex = index


    def initUI(self):
        self.configframe = ConfigFrame(self)
        self.addTab(self.configframe, "&Configuration")

        self.uploadframe = UploadFrame(self)
        self.addTab(self.uploadframe, "Upload")

        self.addTab(QWidget(), "Statistics")
        self.addTab(QWidget(), "Manual Sets")
        self.addTab(QWidget(), "Rule-based Sets")

