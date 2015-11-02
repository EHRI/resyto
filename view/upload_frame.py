#! /usr/bin/env python3
# -*- coding: utf-8 -*-

from PyQt5.QtWidgets import QFrame, QPushButton, QHBoxLayout, QVBoxLayout, QLabel


class UploadFrame(QFrame):

    def __init__(self, parent):
        super().__init__(parent)
        self.initUI()

    def initUI(self):
        # layout
        vert = QVBoxLayout(self)
        hbox1 = QHBoxLayout()

        hbox1.addWidget(QLabel("browse & upload"))
        hbox1.addStretch(1)
        pb_cancel = QPushButton("cancel")
        hbox1.addWidget(pb_cancel)
        pb_next = QPushButton("next")
        hbox1.addWidget(pb_next)

        vert.addLayout(hbox1)
        vert.addStretch(1)

        self.setLayout(vert)


