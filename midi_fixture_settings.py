# -*- coding: utf-8 -*-
#
# This file is part of Linux Show Player
#
# Copyright 2012-2018 Francesco Ceruti <ceppofrancy@gmail.com>
#
# Linux Show Player is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Linux Show Player is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Linux Show Player.  If not, see <http://www.gnu.org/licenses/>.

# pylint: disable=no-name-in-module
from PyQt5.QtCore import Qt#, QT_TRANSLATE_NOOP
from PyQt5.QtWidgets import QGridLayout, QGroupBox, QHeaderView, QPushButton, \
    QTableView, QTableWidget, QVBoxLayout

from lisp.plugins import get_plugin
from lisp.plugins.midi_fixture_control.midi_fixture_select import FixtureSelectDialog
from lisp.plugins.midi_fixture_control.ui import LabelDelegate
from lisp.ui.qdelegates import CheckBoxDelegate, SpinBoxDelegate
from lisp.ui.qmodels import SimpleTableModel
from lisp.ui.settings.pages import SettingsPage
from lisp.ui.ui_utils import translate

class MidiFixtureSettings(SettingsPage):
    Name = "MIDI Fixture Patch"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.setLayout(QVBoxLayout())
        self.layout().setAlignment(Qt.AlignTop)

        self.fixtureSelectDialog = FixtureSelectDialog(parent=self)

        self.patchGroup = QGroupBox(self)
        self.patchGroup.setTitle("MIDI Fixture Patch")
        self.patchGroup.setLayout(QGridLayout())
        self.layout().addWidget(self.patchGroup)

        self.patchListView = MidiPatchView()
        self.patchListModel = SimpleTableModel([
            translate('MidiFixtureSettings', 'MIDI #'),
            translate('MidiFixtureSettings', 'To'),
            translate('MidiFixtureSettings', 'Manufacturer & Model'),
            translate('MidiFixtureSettings', 'Default')
        ])
        self.patchListView.setModel(self.patchListModel)
        self.patchGroup.layout().addWidget(self.patchListView, 0, 0, 1, 3)

        self.addToPatchButton = QPushButton(self.patchGroup)
        self.addToPatchButton.setText('Add')
        self.patchGroup.layout().addWidget(self.addToPatchButton, 1, 0)

        self.editPatchButton = QPushButton(self.patchGroup)
        self.editPatchButton.setText('Edit')
        self.patchGroup.layout().addWidget(self.editPatchButton, 1, 1)

        self.removeFromPatchButton = QPushButton(self.patchGroup)
        self.removeFromPatchButton.setText('Remove')
        self.patchGroup.layout().addWidget(self.removeFromPatchButton, 1, 2)

    def select_fixture(self):
        if self.fixtureSelectDialog.exec_() == self.fixtureSelectDialog.Accepted:
            selected = self.fixtureSelectDialog.selected_fixture()
            if not selected:
                return
            print(selected)

    def getSettings(self):
        pass

    def loadSettings(self):
        pass

class MidiPatchView(QTableView):
    '''Midi patch view.'''

    columns = [
        {
            'delegate': SpinBoxDelegate(minimum=1, maximum=16),
            'width': 64
        }, {
            'delegate': LabelDelegate(),
            'width': 32
        }, {
            'delegate': LabelDelegate()
        }, {
            'delegate': CheckBoxDelegate(),
            'width': 64
        }
    ]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.setSelectionBehavior(QTableWidget.SelectRows)
        self.setSelectionMode(QTableView.SingleSelection)

        self.setShowGrid(False)
        self.setAlternatingRowColors(True)

        self.horizontalHeader().setSectionResizeMode(QHeaderView.Fixed)
        self.horizontalHeader().setStretchLastSection(False)
        self.horizontalHeader().setHighlightSections(False)

        self.verticalHeader().setSectionResizeMode(QHeaderView.Fixed)
        self.verticalHeader().setDefaultSectionSize(24)
        self.verticalHeader().setHighlightSections(False)

        for col_idx, col_spec in enumerate(self.columns):
            self.setItemDelegateForColumn(col_idx, col_spec['delegate'])

    def setModel(self, model):
        super().setModel(model)

        # Widths and resize modes specific to particular columns can only be set
        # *after* a model is applied.
        for col_idx, col_spec in enumerate(self.columns):
            if 'width' in col_spec:
                self.horizontalHeader().resizeSection(col_idx, col_spec['width'])
            else:
                self.horizontalHeader().setSectionResizeMode(col_idx, QHeaderView.Stretch)
