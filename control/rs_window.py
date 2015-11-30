#! /usr/bin/env python3
# -*- coding: utf-8 -*-
from PyQt5.QtWidgets import QMainWindow, QAction, QActionGroup, qApp, QTabWidget, QWidget

from view.config_frame import ConfigFrame
from view.upload_frame import UploadFrame


class RsMainWindow(QMainWindow):

    def __init__(self):
        super().__init__()
        self.create_menu()

        self.tabframe = TabbedFrame(self)
        self.setCentralWidget(self.tabframe)
        self.resize(780, 380)
        self.show()

    def on_tab_choice(self, tabnr):
        self.tabframe.setCurrentIndex(tabnr)
        self.set_tab_menu_enabled(tabnr)

    def set_tab_menu_enabled(self, tabnr):
        for action in self.tab_actions:
            action.setEnabled(True)
        self.tab_actions[tabnr].setEnabled(False)

    def create_menu(self):

        exit_action = QAction("&Exit", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.setStatusTip("Exit application")
        exit_action.triggered.connect(qApp.quit)

        show_configure_action = QAction("&Configure", self)
        show_configure_action.setShortcut("Ctrl+C")
        show_configure_action.setStatusTip("Configure rsync")
        show_configure_action.triggered.connect(lambda: self.on_tab_choice(0))

        show_upload_action = QAction("&Upload", self)
        show_upload_action.setShortcut("Ctrl+U")
        show_upload_action.setStatusTip("Upload files")
        show_upload_action.triggered.connect(lambda: self.on_tab_choice(1))

        show_statistics_action = QAction("&Statistics", self)
        show_statistics_action.setShortcut("Ctrl+S")
        show_statistics_action.setStatusTip("Statistics")
        show_statistics_action.triggered.connect(lambda: self.on_tab_choice(2))

        show_man_sets_action = QAction("&Manual Sets", self)
        show_man_sets_action.setShortcut("Ctrl+M")
        show_man_sets_action.setStatusTip("Manual Sets")
        show_man_sets_action.triggered.connect(lambda: self.on_tab_choice(3))

        show_rule_based_sets_action = QAction("&Rule-based Sets", self)
        show_rule_based_sets_action.setShortcut("Ctrl+R")
        show_rule_based_sets_action.setStatusTip("Rule-based Sets")
        show_rule_based_sets_action.triggered.connect(lambda: self.on_tab_choice(4))

        self.menubar = self.menuBar()
        self.menubar.setNativeMenuBar(True)

        self.fileMenu = self.menubar.addMenu("&File")
        self.fileMenu.addAction(exit_action)             # on mac under [application] > Quit [application]

        self.viewMenu = self.menubar.addMenu("&View")
        self.viewMenu.addAction(show_configure_action)   # on mac under [application] > Preverences
        self.viewMenu.addAction(show_upload_action)
        self.viewMenu.addAction(show_statistics_action)
        self.viewMenu.addAction(show_man_sets_action)
        self.viewMenu.addAction(show_rule_based_sets_action)

        self.tab_actions = list()
        self.tab_actions.append(show_configure_action)      # 0
        self.tab_actions.append(show_upload_action)         # 1
        self.tab_actions.append(show_statistics_action)     # 2
        self.tab_actions.append(show_man_sets_action)       # 3
        self.tab_actions.append(show_rule_based_sets_action) # 4


class TabbedFrame(QTabWidget):

    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.currentChanged.connect(self.__tabchanged)
        self.previndex = -1
        self.initUI()

    def __tabchanged(self, index):
        if self.previndex > -1:
            self.widget(self.previndex).hide()
        self.previndex = index
        self.parent.set_tab_menu_enabled(index)


    def initUI(self):
        self.configframe = ConfigFrame(self)
        self.addTab(self.configframe, "&Configuration")

        self.uploadframe = UploadFrame(self)
        self.addTab(self.uploadframe, "Upload")

        self.addTab(QWidget(), "Statistics")
        self.addTab(QWidget(), "Manual Sets")
        self.addTab(QWidget(), "Rule-based Sets")

