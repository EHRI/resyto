#! /usr/bin/env python3
# -*- coding: utf-8 -*-

import logging

from PyQt5.QtWidgets import QMainWindow, QAction, QActionGroup, qApp, QTabWidget, QWidget
from model.config import Configuration
from view.config_frame import ConfigFrame
from view.export_frame import ExportFrame




class RsMainWindow(QMainWindow):

    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger(__name__)
        self.config = Configuration()
        self.menubar = self.menuBar()
        self.create_menu()

        self.tabframe = TabbedFrame(self)
        self.setCentralWidget(self.tabframe)
        self.resize(self.config.window_width(), self.config.window_height())
        self.show()

    def on_tab_choice(self, tabnr):
        self.tabframe.setCurrentIndex(tabnr)
        self.set_tab_menu_enabled(tabnr)

    def set_tab_menu_enabled(self, tabnr):
        for action in self.tab_actions:
            action.setEnabled(True)
        self.tab_actions[tabnr].setEnabled(False)

    def create_menu(self):

        exit_action = QAction(_("&Exit"), self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.setStatusTip(_("Exit application"))
        exit_action.triggered.connect(qApp.quit)

        show_configure_action = QAction(_("&Configure"), self)
        show_configure_action.setShortcut("Ctrl+C")
        show_configure_action.setStatusTip("Configure rsync")
        show_configure_action.triggered.connect(lambda: self.on_tab_choice(0))

        show_export_action = QAction(_("&Export"), self)
        show_export_action.setShortcut("Ctrl+E")
        show_export_action.setStatusTip(_("Export files"))
        show_export_action.triggered.connect(lambda: self.on_tab_choice(1))

        show_statistics_action = QAction(_("&Statistics"), self)
        show_statistics_action.setShortcut("Ctrl+S")
        show_statistics_action.setStatusTip(_("Statistics"))
        show_statistics_action.triggered.connect(lambda: self.on_tab_choice(2))

        show_man_sets_action = QAction(_("&Manual Sets"), self)
        show_man_sets_action.setShortcut("Ctrl+M")
        show_man_sets_action.setStatusTip(_("Manual Sets"))
        show_man_sets_action.triggered.connect(lambda: self.on_tab_choice(3))

        show_rule_based_sets_action = QAction(_("&Rule-based Sets"), self)
        show_rule_based_sets_action.setShortcut("Ctrl+R")
        show_rule_based_sets_action.setStatusTip(_("Rule-based Sets"))
        show_rule_based_sets_action.triggered.connect(lambda: self.on_tab_choice(4))


        self.menubar.setNativeMenuBar(True)

        self.fileMenu = self.menubar.addMenu(_("&File"))
        self.fileMenu.addAction(exit_action)             # on mac under [application] > Quit [application]

        self.viewMenu = self.menubar.addMenu(_("&View"))
        self.viewMenu.addAction(show_configure_action)   # on mac under [application] > Preverences
        self.viewMenu.addAction(show_export_action)
        self.viewMenu.addAction(show_statistics_action)
        self.viewMenu.addAction(show_man_sets_action)
        self.viewMenu.addAction(show_rule_based_sets_action)

        self.tab_actions = list()
        self.tab_actions.append(show_configure_action)      # 0
        self.tab_actions.append(show_export_action)         # 1
        self.tab_actions.append(show_statistics_action)     # 2
        self.tab_actions.append(show_man_sets_action)       # 3
        self.tab_actions.append(show_rule_based_sets_action) # 4

    def close(self):
        self.logger.debug("window closing")
        self.config.set_window_height(self.height())
        self.config.set_window_width(self.width())
        self.config.persist()
        self.tabframe.close()


class TabbedFrame(QTabWidget):

    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.currentChanged.connect(self.__tabchanged)
        self.previndex = -1
        self.configframe = ConfigFrame(self)
        self.exportframe = ExportFrame(self)
        self.init_ui()

    def __tabchanged(self, index):
        if self.previndex > -1:
            self.widget(self.previndex).hide()

        self.widget(index).show()
        self.previndex = index
        self.parent.set_tab_menu_enabled(index)

    def init_ui(self):
        self.addTab(self.configframe, _("&Configuration"))

        self.addTab(self.exportframe, _("&Export"))

        self.addTab(QWidget(), _("Statistics"))
        self.addTab(QWidget(), _("Manual Sets"))
        self.addTab(QWidget(), _("Rule-based Sets"))

    def close(self):
        self.logger.debug("tabframe closing")
        self.currentWidget().close()

