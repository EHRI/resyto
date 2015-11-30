#! /usr/bin/env python3
# -*- coding: utf-8 -*-

from PyQt5.QtWidgets import QFrame, QPushButton, QGridLayout, QHBoxLayout, QLabel, QFileDialog, QTextEdit
from view.config_frame import Configuration
from resync_publisher.ehri_client import ResourceSyncPublisherClient
from resync.resource_list_builder import ResourceListBuilder


class UploadFrame(QFrame):

    def get_existing_resync_file(self, resync_file):
        return 'file://'+self.config.get_cfg_resync_dir()+'/'+resync_file

    def __init__(self, parent):
        super().__init__(parent)
        self.config = Configuration()
        self.textEdit = QTextEdit()
        self.init_ui()
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
        pb_browse.clicked.connect(self.show_dialog)
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
        lb_r_list = QLabel(self.get_existing_resync_file('resourcelist.xml'))
        lb_c_list = QLabel(self.get_existing_resync_file('changelist.xml'))
        grid_right.addWidget(lb_r_list, 4, 1)
        grid_right.addWidget(lb_c_list, 5, 1)

        pb_cancel = QPushButton(_("cancel"))
        grid_right.addWidget(pb_cancel, 6, 1)

        vert.addLayout(grid_left)
        vert.addLayout(grid_right)
        vert.addStretch(1)

        self.setLayout(vert)

    def resync_change_list(self):
        c = ResourceSyncPublisherClient(checksum=True)
        args = [self.config.get_cfg_urlprefix(), self.config.get_cfg_resource_dir()]
        c.set_mappings(args)
        rl = c.calculate_changelist(paths=self.data, resource_sitemap=self.get_existing_resync_file('resourcelist.xml'), changelist_sitemap=self.get_existing_resync_file('changelist.xml'))
        self.textEdit.setText(rl.as_xml())

    def show_dialog(self):
        filenames = QFileDialog.getOpenFileNames(
                        self,
                        _("Select one or more files to open"),
                        self.config.get_cfg_resource_dir()
                        )

        # print(filenames)
        self.data = ",".join(filenames[0])
        # print(self.data)
        self.textEdit.setText(self.data)

    def resync_resource_list(self):
        c = ResourceSyncPublisherClient(checksum=True)
        args = [self.config.get_cfg_urlprefix(), self.config.get_cfg_resource_dir()]
        c.set_mappings(args)
        rl = c.build_resource_list(paths=self.data)
        self.textEdit.setText(rl.as_xml())

