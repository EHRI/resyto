#! /usr/bin/env python3
# -*- coding: utf-8 -*-

import os
from pathlib import PurePath
from PyQt5.QtWidgets import QFrame, QPushButton, QGridLayout, QHBoxLayout, QVBoxLayout, QLabel, QDialog, QFileDialog, \
    QFileSystemModel, QTreeView, QAbstractItemView, QTextEdit
from view.config_frame import Configuration
from resync_publisher.ehri_client import ResourceSyncPublisherClient
from resync.resource_list_builder import ResourceListBuilder


class UploadFrame(QFrame):

    def get_existing_resync_file(self, resync_file):
        # get the existing resync_file as file URI.
        #return 'file://'+self.config.get_cfg_resync_dir()+'/'+resync_file
        p = PurePath(self.config.cfg_resync_dir(), resync_file)
        return p.as_uri()

    def __init__(self, parent):
        super().__init__(parent)
        self.config = Configuration()
        self.textEdit = QTextEdit()
        self.init_ui()
        self.explorer = Explorer(self)
        self.data = ''

    def init_ui(self):
        # layout
        vert = QHBoxLayout(self)
        grid_left = QGridLayout()
        grid_left.setColumnMinimumWidth(1, 180)

        grid_left.addWidget(QLabel(_("browse & upload")), 1, 1,)
        self.textEdit.setMinimumWidth(80)
        grid_left.addWidget(self.textEdit, 2, 1)

        grid_right = QGridLayout()
        grid_right.setColumnMinimumWidth(1, 40)

        pb_browse = QPushButton(_("browse"))
        # pb_browse.clicked.connect(self.show_dialog)
        pb_browse.clicked.connect(self.show_explorer)
        grid_right.addWidget(pb_browse, 1, 1)

        pb_resourcelist = QPushButton(_("Create ResourceList"))
        pb_resourcelist.clicked.connect(self.resync_resource_list)
        # _('Welcome, {name}').format(name=username)
        pb_resourcelist.setToolTip(_('Create ResourceList based on selected files'))
        grid_right.addWidget(pb_resourcelist, 2, 1)

        pb_changelist = QPushButton(_("Create ChangeList"))
        pb_changelist.clicked.connect(self.resync_change_list)
        pb_changelist.setToolTip(_('Create ChangeList based on selected files and resync Lists'))
        grid_right.addWidget(pb_changelist, 3, 1)

        # could be part of tooltip instead?
        self.lb_r_list = QLabel(self.get_existing_resync_file('resourcelist.xml'))
        self.lb_c_list = QLabel(self.get_existing_resync_file('changelist.xml'))
        grid_right.addWidget(self.lb_r_list, 4, 1)
        grid_right.addWidget(self.lb_c_list, 5, 1)

        pb_cancel = QPushButton(_("cancel"))
        grid_right.addWidget(pb_cancel, 6, 1)

        vert.addLayout(grid_left)
        vert.addLayout(grid_right)
        vert.addStretch(1)

        self.setLayout(vert)

    def show(self):
        # dynamically reflect current state of config
        self.lb_r_list.setText(self.get_existing_resync_file('resourcelist.xml'))
        self.lb_c_list.setText(self.get_existing_resync_file('changelist.xml'))

    def show_dialog(self):
        filenames = QFileDialog.getOpenFileNames(
                        self,
                        _("Select one or more files to open"),
            self.config.cfg_resource_dir()
                        )

        # print(filenames)
        self.data = ",".join(filenames[0])
        # print(self.data)
        self.textEdit.setText(self.data)

    def show_explorer(self):
        result = self.explorer.exec_()
        if result:
            print(result)
            filenames = self.explorer.paths()
            self.data = ",".join(filenames)
            self.textEdit.setText(str(len(filenames)) + " resources")

    def resync_resource_list(self):
        c = ResourceSyncPublisherClient(checksum=True)
        args = [self.config.cfg_urlprefix(), self.config.cfg_resource_dir()]
        c.set_mappings(args)
        rl = c.build_resource_list(paths=self.data)
        self.textEdit.setText(rl.as_xml())

    def resync_change_list(self):
        c = ResourceSyncPublisherClient(checksum=True)
        args = [self.config.cfg_urlprefix(), self.config.cfg_resource_dir()]
        c.set_mappings(args)
        rl = c.calculate_changelist(paths=self.data, resource_sitemap=self.get_existing_resync_file('resourcelist.xml'), changelist_sitemap=self.get_existing_resync_file('changelist.xml'))
        self.textEdit.setText(rl.as_xml())


class Explorer(QDialog):

    def __init__(self, parent):
        super().__init__(parent)
        self.setModal(True)
        self.setSizeGripEnabled(True)
        self.config = Configuration()
        self.init_ui()
        #self.show()

    def init_ui(self):
        # layout
        vert = QVBoxLayout(self)
        vert.setContentsMargins(0, 0, 0, 0)

        p_top = QHBoxLayout()
        self.model = QFileSystemModel()
        self.model.setRootPath(self.config.cfg_resource_dir())

        self.view = QTreeView()
        self.view.setModel(self.model)
        self.view.setRootIndex(self.model.index(self.model.rootPath()))
        self.view.setAlternatingRowColors(True)
        self.view.setSelectionMode(QAbstractItemView.MultiSelection)
        p_top.addWidget(self.view)

        p_bottom = QHBoxLayout()
        p_bottom.addStretch(1)
        pb_ok = QPushButton(_("OK"))
        pb_ok.setAutoDefault(True)
        pb_ok.clicked.connect(self.accept)
        p_bottom.addWidget(pb_ok)

        pb_cancel = QPushButton(_("Cancel"))
        pb_cancel.clicked.connect(self.reject)
        p_bottom.addWidget(pb_cancel)

        vert.addLayout(p_top)
        vert.addLayout(p_bottom)

        self.setLayout(vert)
        self.resize(self.config.explorer_width(), self.config.explorer_height())
        width = self.view.width()  - 50
        self.view.setColumnWidth(0, width/2)
        self.view.setColumnWidth(1, width/6)
        self.view.setColumnWidth(2, width/6)
        self.view.setColumnWidth(3, width/6)

    def paths(self):
        indexes = self.view.selectedIndexes()
        s = set()
        # there are multiple indexes pointing to the same file...
        for index in indexes:
            s.add(self.model.filePath(index))
        li = list()
        for path in s:
            if os.path.isdir(path):
                #print("isDir", path)
                for root, directories, filenames in os.walk(path):
                    for filename in filenames:
                        if not filename.startswith('.'):
                            li.append(os.path.join(root, filename))
            elif os.path.isfile(path):
                #print("isFile", path)
                li.append(path)
            else:
                print("isUnknownThing", path)

        return li

    def closeEvent(self, QCloseEvent):
        self.config.set_explorer_width(self.width())
        self.config.set_explorer_height(self.height())
        self.config.persist()





