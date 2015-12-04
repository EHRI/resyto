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
        self.explorer = Explorer(self)

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
            filenames = self.explorer.selected_file_set()
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


# so much for duck typing..
class FilenameFilter(object):

    def accept(self, filename):
        return not filename.startswith('.')


class Explorer(QDialog):

    def __init__(self, parent, window_title=_("Select resources"),
                 subtitle=_("Select files and/or folders to include")):
        super().__init__(parent)
        self.setModal(True)
        self.setSizeGripEnabled(True)
        self.setWindowTitle(window_title)
        self.subtitle = subtitle
        self.file_set = set()
        self.config = Configuration()
        self.__init_ui__()
        self.filename_filter = FilenameFilter()
        #self.show()

    def __init_ui__(self):
        # layout
        vert = QVBoxLayout(self)
        vert.setContentsMargins(0, 0, 0, 0)

        resource_dir = self.config.cfg_resource_dir()

        p_top = QVBoxLayout()
        lb_subtitle = QLabel(self.subtitle)
        lb_subtitle.setContentsMargins(10, 10, 10, 0)
        p_top.addWidget(lb_subtitle)

        self.model = QFileSystemModel()
        self.model.setRootPath(resource_dir)

        self.view = QTreeView()
        self.view.setModel(self.model)
        self.view.setRootIndex(self.model.index(self.model.rootPath()))
        self.view.setAlternatingRowColors(True)
        self.view.setSelectionMode(QAbstractItemView.MultiSelection)
        self.view.selectionModel().selectionChanged.connect(self.selection_changed)
        p_top.addWidget(self.view)

        p_info = QHBoxLayout()
        lb_resource = QLabel(_("resource dir") + ": " + resource_dir)
        lb_resource.setContentsMargins(10, 0, 10, 0)

        self.lb_selection_count = QLabel(str(self.selected_file_count()) + " " + _("resources selected"))
        self.lb_selection_count.setContentsMargins(10, 0, 10, 0)

        p_info.addWidget(self.lb_selection_count)
        p_info.addStretch(1)
        p_info.addWidget(lb_resource)

        p_top.addLayout(p_info)

        p_bottom = QHBoxLayout()

        self.pb_toggle_select = QPushButton(_("Deselect all"))
        self.pb_toggle_select.clicked.connect(self.toggle_select)
        self.pb_toggle_select.setEnabled(self.selected_file_count() > 0)
        p_bottom.addWidget(self.pb_toggle_select)

        p_bottom.addStretch(1)
        self.pb_ok = QPushButton(_("OK"))
        self.pb_ok.setAutoDefault(True)
        self.pb_ok.clicked.connect(self.accept)
        p_bottom.addWidget(self.pb_ok)

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

    def __persist__(self):
        # persist properties of the explorer
        self.config.set_explorer_width(self.width())
        self.config.set_explorer_height(self.height())
        self.config.persist()

    def __compute_filenames__(self, item_selection):
        # item_selection: a QItemSelection
        # return corresponding absolute filenames as a set, including filenames in underlying folders
        s = set()
        for index in item_selection.indexes():
            print(index)
            # we have an index for each column in the model
            if index.column() == 0:
                path = index.model().filePath(index)
                if os.path.isdir(path):
                    for root, directories, filenames in os.walk(path):
                        for filename in filenames:
                            if self.filename_filter.accept(filename):
                                s.add(os.path.join(root, filename))
                elif os.path.isfile(path):
                    s.add(path)
                else:
                    print("isUnknownThing", path)
        return s

    def showEvent(self, QShowEvent):
        # print("showing: ")
        #self.pb_ok.setFocus()
        pass

    def set_filename_filter(self, filename_filter):
        # set the FilenameFilter
        self.filename_filter = filename_filter

    def selected_file_count(self):
        return len(self.file_set)

    def selected_file_set(self):
        return frozenset(self.file_set)

    def selection_changed(self, selected, deselected):
        # # selected, deselected: PyQt5.QtCore.QItemSelection
        # print("selected")
        # for index in selected.indexes():
        #     # index: PyQt5.QtCore.QModelIndex.
        #     #print(index.row(), index.column(), index.data())
        #     if index.column() == 0:
        #         print(self.model.filePath(index))
        #         self.view.expand(index)
        #     #print(index.model(), self.model) # same
        #     #print()
        
        selected_filenames = self.__compute_filenames__(selected)
        self.file_set.update(selected_filenames)
        deselected_filenames = self.__compute_filenames__(deselected)
        self.file_set.difference_update(deselected_filenames)

        self.pb_toggle_select.setEnabled(self.selected_file_count() > 0)
        self.lb_selection_count.setText(str(self.selected_file_count()) + " " + _("resources selected"))

    def toggle_select(self):
        self.view.selectionModel().clear()

    def hideEvent(self, QHideEvent):
        self.__persist__()







