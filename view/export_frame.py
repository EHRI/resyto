#! /usr/bin/env python3
# -*- coding: utf-8 -*-

import datetime, logging
import operator
import os
import webbrowser
import zipfile
from pathlib import PurePath

from PyQt5.QtCore import QAbstractTableModel, Qt
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import QFrame, QPushButton, QHBoxLayout, QVBoxLayout, QLabel, QDialog, QFileSystemModel, QTreeView, QAbstractItemView, \
    QTableView, QSplitter, QMessageBox
#from signal import *
from view.config_frame import Configuration
#from blaa.ehri_client import ResourceSyncPublisherClient
from resync_publisher.ehri_client import ResourceSyncPublisherClient
#from resync_a.resource_list_builder import ResourceListBuilder, Resource


CHANGELIST_XML = "changelist.xml"
RESOURCELIST_XML = "resourcelist.xml"
RESOURCESYNC_ZIP = "resourcesync.zip"

def file_details(s):
    l = list()
    for path in s:
        l.append([path, os.path.basename(path), os.path.getsize(path), os.path.getmtime(path)])
    return l


class ExportFrame(QFrame):

    def get_existing_resync_file(self, resync_file):
        # get the existing resync_file as file URI.
        #return 'file://'+self.config.get_cfg_resync_dir()+'/'+resync_file
        p = PurePath(self.config.core_metadata_dir(), resync_file)
        return p.as_uri()

    def __init__(self, parent):
        super().__init__(parent)
        self.logger = logging.getLogger(__name__)
        self.config = Configuration()
        self.filenames = []
        self.data = ''

        # left part of frame
        header_left = [_("Relative Path"), _("Name"), _("Size"), _("Date Modified")]
        self.file_model = FileTableModel(self, header_left, [])

        self.file_view = QTableView()
        self.file_view.setModel(self.file_model)
        self.file_view.setSortingEnabled(True)
        self.file_view.setAlternatingRowColors(True)
        self.file_view.setShowGrid(False)

        # adjustments
        self.file_view.verticalHeader().setDefaultSectionSize(22)
        #self.file_view.horizontalHeader().setDefaultSectionSize(self.file_view.width()/len(header))
        #self.file_view.horizontalHeader().setStretchLastSection(True)
        self.file_view.setSelectionMode(QAbstractItemView.SingleSelection)
        self.file_view.setSelectionBehavior(QAbstractItemView.SelectRows)

        self.file_view.doubleClicked.connect(self.file_view_doubleclicked)
        #self.file_view.clicked.connect(self.file_view_clicked)
        self.file_view.selectionModel().selectionChanged.connect(self.file_view_selection_changed)
        #self.file_view.setContextMenuPolicy(Qt.CustomContextMenu)
        #self.file_view.customContextMenuRequested.connect(self.file_view_context_menu_requested)

        #self.lb_nsfc = QLabel("")
        self.lb_path = QLabel("")
        self.lb_path.setFont(QFont('SansSerif', 10))

        self.pb_select = QPushButton(_("Select"))
        self.pb_select.clicked.connect(self.show_explorer)

        # right part of frame
        header_right = [_("Set Name"), _("Files"), _("New Files"), _("Update Files"), _("Unchanged Files")]
        self.overview_model = OverviewTableModel(self, header_right, [])
        self.overview = QTableView()
        self.overview.setModel(self.overview_model)
        self.overview.setAlternatingRowColors(True)
        self.overview.setShowGrid(False)

        self.overview.verticalHeader().setDefaultSectionSize(22)

        self.pb_publish = QPushButton(_("Publish"))
        self.pb_publish.clicked.connect(self.pb_publish_clicked)

        self.pb_zip = QPushButton(_("Create Zip"))
        self.pb_zip.clicked.connect(self.pb_zip_clicked)

        self.__init_ui__()

    def __init_ui__(self):

        vbox = QVBoxLayout()

        splitter = QSplitter()

        splitter.addWidget(self.file_view)
        splitter.addWidget(self.overview)

        vbox.addWidget(splitter, 1)
        vbox.addWidget(self.lb_path)

        button_box = QHBoxLayout()
        button_box.addWidget(self.pb_select)
        button_box.addStretch(1)
        button_box.addWidget(self.pb_publish)
        button_box.addWidget(self.pb_zip)
        vbox.addLayout(button_box)

        self.setLayout(vbox)

    def file_view_doubleclicked(self, index):
        path = self.file_model.full_path(index.row())
        webbrowser.open_new(PurePath(path).as_uri())

    def file_view_clicked(self, index):
        pass

    def file_view_selection_changed(self, selected, deselected):
        # selected, deselected: PyQt5.QtCore.QItemSelection
        sindexes = selected.indexes()
        if len(sindexes) > 0:
            index = sindexes[0]
            path = self.file_model.full_path(index.row())
            self.lb_path.setText(path)
        else:
            self.lb_path.setText("")

    def pb_zip_clicked(self):
        path = os.path.join(os.path.dirname(self.config.core_metadata_dir()), RESOURCESYNC_ZIP)
        self.logger.debug("Creating zip file at %s", path)
        ziph = zipfile.ZipFile(path, 'w', zipfile.ZIP_DEFLATED)
        filename_filter = FilenameFilter()
        src = self.config.core_metadata_dir()
        abs_src = os.path.abspath(src)
        for dirname, subdirs, files in os.walk(src):
            for filename in files:
                if filename_filter.accept(filename):
                    absname = os.path.abspath(os.path.join(dirname, filename))
                    arcname = absname[len(abs_src) + 1:]
                    self.logger.debug('zipping %s as %s' % (os.path.join(dirname, filename),
                                            arcname))
                    ziph.write(absname, arcname)

        ziph.close()
        self.logger.debug("Ready creating zip file at %s", path)
        msgbox = QMessageBox()
        msgbox.setText("Zip file created: \n" + path)
        msgbox.exec_()

    def show(self):
        self.explorer = Explorer(self)

    def show_explorer(self):
        result = self.explorer.exec_()
        if result:
            self.filenames = self.explorer.selected_file_set()
            self.data = ",".join(self.filenames)
            self.file_model.setNewData(file_details(self.filenames))
            self.file_view.selectionModel().clear()
            self.lb_path.setText("")

    def pb_publish_clicked(self):
            if self.config.core_strategy() == 0:
                self.resync_resource_list()
            else:
                self.resync_change_list(self.filenames)

    def resync_resource_list(self):
        c = ResourceSyncPublisherClient(checksum=True)
        args = [self.config.core_url_prefix(), self.config.core_resource_dir()]
        c.set_mappings(args)
        rl = c.build_resource_list(paths=self.data)
        overview_data = [(_("total"), str(len(rl)), str(len(rl)), str(0), str(0))]
        self.overview_model.setNewData(overview_data)
        rl_path = os.path.join(self.config.core_metadata_dir(), RESOURCELIST_XML)
        rl.write(rl_path)
        # webbrowser.open_new(PurePath(rl_path).as_uri())


    def resync_change_list(self, filenames):
        c = ResourceSyncPublisherClient(checksum=True)
        args = [self.config.core_url_prefix(), self.config.core_resource_dir()]
        c.set_mappings(args)
        cl_path = os.path.join(self.config.core_metadata_dir(), CHANGELIST_XML)
        cl = c.calculate_changelist(paths=self.data, resource_sitemap=self.get_existing_resync_file(RESOURCELIST_XML),
                                    changelist_sitemap=self.get_existing_resync_file(CHANGELIST_XML),
                                    outfile=cl_path)
        # the calculating should be done in resync_a, not in the GUI
        file_count = len(filenames)
        created_count = 0
        updated_count = 0

        for resource in cl.resources:
            if resource.change == "created":
                created_count += 1
            elif resource.change == "updated":
                updated_count += 1

        # this is not the correct computation..
        unchanged_count = file_count - created_count - updated_count

        overview_data = [(_("total"), str(file_count), str(created_count), str(updated_count), str(unchanged_count))]
        self.overview_model.setNewData(overview_data)

        # webbrowser.open_new(PurePath(cl_path).as_uri())


class FileTableModel(QAbstractTableModel):

    def __init__(self, parent, header, data, *args):
        QAbstractTableModel.__init__(self, parent, *args)
        self.header = header
        self.data = data

    def rowCount(self, parent):
        return len(self.data)

    def columnCount(self, parent):
        return len(self.header)

    def headerData(self, col, orientation, role):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return self.header[col]
        return None

    def data(self, index, role):
        if not index.isValid():
            return None
        if role == Qt.TextAlignmentRole and index.column() >= 2:
            return Qt.AlignRight + Qt.AlignVCenter
        # if role == Qt.ToolTipRole:
        #     return self.data[index.row()][0] # full path

        if role != Qt.DisplayRole:
            return None

        # Qt.DisplayRole
        d = self.data[index.row()][index.column()]
        if index.column() == 0:
            d = os.path.relpath(os.path.dirname(d), self.parent().config.core_resource_dir())
        elif index.column() == 3:
            d = str(datetime.datetime.fromtimestamp(d))
        return d

    def sort(self, col, order):
        """sort table by given column number col"""
        self.layoutAboutToBeChanged.emit()
        self.data = sorted(self.data, key=operator.itemgetter(col))
        if order == Qt.DescendingOrder:
            self.data.reverse()
        self.layoutChanged.emit()

    def setNewData(self, data):
        self.layoutAboutToBeChanged.emit()
        self.data = sorted(data, key=operator.itemgetter(0))
        self.layoutChanged.emit()
        for index, item in enumerate(self.header):
            self.parent().file_view.resizeColumnToContents(index)

    def full_path(self, row):
        return self.data[row][0]


class OverviewTableModel(QAbstractTableModel):

    def __init__(self, parent, header, data, *args):
        QAbstractTableModel.__init__(self, parent, *args)
        self.header = header
        self.data = data

    def rowCount(self, parent):
        return len(self.data)

    def columnCount(self, parent):
        return len(self.header)

    def headerData(self, col, orientation, role):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return self.header[col]
        return None

    def data(self, index, role):
        if role == Qt.TextAlignmentRole and index.column() >= 1:
            return Qt.AlignRight + Qt.AlignVCenter

        if role != Qt.DisplayRole:
            return None

        # Qt.DisplayRole
        d = self.data[index.row()][index.column()]
        return d

    def setNewData(self, data):
        self.layoutAboutToBeChanged.emit()
        self.data = sorted(data, key=operator.itemgetter(0))
        self.layoutChanged.emit()
        for index, item in enumerate(self.header):
            self.parent().file_view.resizeColumnToContents(index)


# so much for duck typing..
class FilenameFilter(object):

    def accept(self, filename):
        return not filename.startswith('.')


class Explorer(QDialog):

    def __init__(self, parent, window_title=_("Select resources"),
                 subtitle=_("Select files and/or folders to include")):
        super().__init__(parent)
        self.logger = logging.getLogger(__name__)
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

        resource_dir = self.config.core_resource_dir()

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
        self.view.collapsed.connect(self.item_collapsed)
        self.view.expanded.connect(self.item_expanded)
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

        self.pb_deselect = QPushButton(_("Deselect all"))
        self.pb_deselect.clicked.connect(self.pb_deselect_clicked)
        self.pb_deselect.setEnabled(self.selected_file_count() > 0)
        p_bottom.addWidget(self.pb_deselect)

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
                    self.logger.warn("isUnknownThing", path)
        return s

    def showEvent(self, QShowEvent):
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
        # selected, deselected: PyQt5.QtCore.QItemSelection
        selected_filenames = self.__compute_filenames__(selected)
        self.file_set.update(selected_filenames)
        deselected_filenames = self.__compute_filenames__(deselected)
        self.file_set.difference_update(deselected_filenames)

        self.pb_deselect.setEnabled(self.selected_file_count() > 0)
        self.lb_selection_count.setText(str(self.selected_file_count()) + " " + _("resources selected"))

    def item_expanded(self, index):
        # index: a QModelIndex
        # show all child items selected/deselected in accordance with state of parent folder
        pass

    def item_collapsed(self, index):
        pass

    def pb_deselect_clicked(self):
        self.view.selectionModel().clear()

    def hideEvent(self, QHideEvent):
        self.__persist__()







