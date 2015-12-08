#! /usr/bin/env python3
# -*- coding: utf-8 -*-

import i18n, os, gettext

from PyQt5.QtWidgets import QComboBox, QFrame, QGridLayout, QLabel, QLineEdit, QPushButton, QHBoxLayout, \
    QVBoxLayout, QFileDialog, QSpacerItem, QButtonGroup, QRadioButton, QAbstractButton, QGroupBox
from model.config import Configuration


tt_sourcedesc = _("Source Description: \ndescription of the institute publishing the resources and the content of the resources in this set (resourcelist), to be attached to the sourcedescription in a 'describedby' relation")


class ConfigFrame(QFrame):

    def __init__(self, parent):
        super().__init__(parent)
        self.config = Configuration()
        self.le_resourcedir = QLineEdit(self.config.cfg_resource_dir())

        self.le_resyncdir = QLineEdit(self.config.cfg_resync_dir())
        self.le_sourcedesc = QLineEdit(self.config.cfg_sourcedesc())
        self.le_urlprefix = QLineEdit(self.config.cfg_urlprefix())
        # self.language_choice = QLabel(_("Interface Language"), self)
        self.init_ui()

    def init_ui(self):
        # layout
        vert = QVBoxLayout(self)

        grid1 = QGridLayout()
        grid1.setContentsMargins(0, 0, 0, 0) # left, top, right, bottom

        self.pb_resourcedir = QPushButton(_("Browse"))
        self.pb_resourcedir.clicked.connect(self.pb_resourcedir_clicked)
        grid1.addWidget(QLabel(_("Resource directory")), 1, 1)
        grid1.addWidget(self.le_resourcedir, 1, 2)
        grid1.addWidget(self.pb_resourcedir, 1, 3)

        pb_resyncdir = QPushButton(_("Browse"))
        pb_resyncdir.clicked.connect(self.pb_resyncdir_clicked)
        grid1.addWidget(QLabel(_("Resync directory")), 2, 1)
        grid1.addWidget(self.le_resyncdir, 2, 2)
        grid1.addWidget(pb_resyncdir, 2, 3)

        # language_combo = QComboBox(self)
        # for dirname in i18n.get_languages():
        #     language_combo.addItem(dirname)
        # language_combo.activated[str].connect(self.cb_language_changed)
        # grid1.addWidget(self.language_choice, 3, 1)
        # grid1.addWidget(language_combo, 3, 2)

        self.le_sourcedesc.setToolTip(tt_sourcedesc)
        grid1.addWidget(QLabel(_("Source description")), 3, 1)
        grid1.addWidget(self.le_sourcedesc, 3, 2)
        grid1.addItem(QSpacerItem(87, 21), 3, 3)

        self.le_urlprefix.setToolTip(_("The url domain to be used in the resync files"))
        grid1.addWidget(QLabel(_("URL prefix")), 4, 1)
        grid1.addWidget(self.le_urlprefix, 4, 2)
        grid1.addItem(QSpacerItem(87, 21), 4, 3)

        vert.addLayout(grid1)

        strat_vert = QVBoxLayout()
        strat_vert.addWidget(QLabel(_("Strategy")))
        self.strat_group = QButtonGroup(strat_vert)

        strat_1 = QRadioButton(_("resourcelist"))
        strat_2 = QRadioButton(_("resourcelist + changelist"))

        self.strat_group.addButton(strat_1, 0)
        self.strat_group.addButton(strat_2, 1)
        self.strat_group.button(self.config.cfg_strategy()).setChecked(True)
        strat_vert.addWidget(strat_1)
        strat_vert.addWidget(strat_2)
        #self.strat_group.buttonToggled.connect(self.bg_strategy_toggled)
        vert.addLayout(strat_vert)


        vert.addStretch(1)

        # hbox = QHBoxLayout()
        # hbox.addStretch(1)
        #
        # vert.addLayout(hbox)

        self.setLayout(vert)

    def __persist_config__(self):
        self.config.set_cfg_resource_dir(self.le_resourcedir.text())
        self.config.set_cfg_resync_dir(self.le_resyncdir.text())
        self.config.set_cfg_sourcedesc(self.le_sourcedesc.text())
        self.config.set_cfg_urlprefix(self.le_urlprefix.text())
        self.config.set_cfg_strategy(self.strat_group.checkedId())
        self.config.persist()

    def pb_resourcedir_clicked(self):
        self.le_resourcedir.setFocus()
        # "Unable to simultaneously satisfy constraints:..." as warning is a QT bug:
        # https://bugreports.qt.io/browse/QTBUG-43248
        filename = QFileDialog.getExistingDirectory(self, _("Resource Directory"), self.le_resourcedir.text())
        if filename != "": # user cancelled
            self.le_resourcedir.setText(filename)

    def pb_resyncdir_clicked(self):
        self.le_resyncdir.setFocus()
        # "Unable to simultaneously satisfy constraints:..." as warning is a QT bug:
        # https://bugreports.qt.io/browse/QTBUG-43248
        filename = QFileDialog.getExistingDirectory(self, _("Resync Directory"), self.le_resyncdir.text())
        if filename != "": # user cancelled
            self.le_resyncdir.setText(filename)

    # def cb_language_changed(self, text):
    #     print(text)
    #     print(os.path.abspath(gettext.find(i18n.APP_NAME, localedir=i18n.LOCALE_DIR, languages=[text])))
    #     # gettext.translation(i18n.APP_NAME, localedir=i18n.LOCALE_DIR, languages=[text]).install()
    #     i18n.set_language(text)
    #     # repaint window application ??
    #     print(_("browse"))

    def hide(self):
        self.__persist_config__()

    def close(self):
        self.__persist_config__()


