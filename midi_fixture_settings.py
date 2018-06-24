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
        self.patchListModel = MidiPatchModel([
            translate('MidiFixtureSettings', 'MIDI #'),
            translate('MidiFixtureSettings', 'To'),
            translate('MidiFixtureSettings', 'Manufacturer & Model'),
            translate('MidiFixtureSettings', 'Default')
        ])
        self.patchListView.setModel(self.patchListModel)
        self.patchGroup.layout().addWidget(self.patchListView, 0, 0, 1, 3)

        self.addToPatchButton = QPushButton(self.patchGroup)
        self.addToPatchButton.setText('Add')
        self.addToPatchButton.clicked.connect(self._add_patch)
        self.patchGroup.layout().addWidget(self.addToPatchButton, 1, 0)

        self.editPatchButton = QPushButton(self.patchGroup)
        self.editPatchButton.setText('Edit')
        self.patchGroup.layout().addWidget(self.editPatchButton, 1, 1)

        self.removeFromPatchButton = QPushButton(self.patchGroup)
        self.removeFromPatchButton.setText('Remove')
        self.patchGroup.layout().addWidget(self.removeFromPatchButton, 1, 2)

    def _add_patch(self):
        fixture_id = self.select_fixture()
        if not fixture_id:
            return

        library = get_plugin('MidiFixtureControl').get_library()
        fixture_profile = library.get_device_profile(fixture_id)

        fixture_label = '{manu} {model}'.format_map({
            'manu': library.get_manufacturer_list()[fixture_profile['manufacturer']],
            'model': fixture_profile['name']
        })

        self.patchListModel.appendPatch(fixture_label, fixture_profile['width'], fixture_id)

    def select_fixture(self):
        if self.fixtureSelectDialog.exec_() == self.fixtureSelectDialog.Accepted:
            selected = self.fixtureSelectDialog.selected_fixture()
            if selected:
                return selected
        return False

    def getSettings(self):
        pass

    def loadSettings(self):
        pass

class MidiPatchView(QTableView):
    '''Midi patch view.'''

    columns = [
        {
            'delegate': SpinBoxDelegate(minimum=1, maximum=16),
            'width': 72
        }, {
            'delegate': LabelDelegate(),
            'width': 28
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

class MidiPatchModel(SimpleTableModel):
    def __init__(self, columns):
        super().__init__(columns)
        self.address_space = [False for i in range(16)]
        self.fixture_patch = [None for i in range(16)]
        print("AS : " + str(self.address_space))

    def appendPatch(self, fixture_label, fixture_width, fixture_id):
        fixture_address = self._find_space(0, fixture_width, False)
        if fixture_address == -1:
            return
        fixture_end_address = fixture_address + fixture_width

        self.fixture_patch[fixture_address] = fixture_id
        for idx in range(fixture_address, fixture_end_address):
            self.address_space[idx] = True

        super().appendRow(fixture_address + 1, fixture_end_address, fixture_label, self.rowCount() == 0)

    def removeRow(self, row):
        print("AS : " + str(self.address_space))
        super().removeRow(row)

    def setData(self, index, value, role=Qt.DisplayRole):
        if not index.isValid():
            return False

        if index.column() == 0:
            print(value)

        print("AS : " + str(self.address_space))
        return super().setData(index, value, role)

    def _find_space(self, start, width, loop=True):

        def _checkWidth(idx):
            for idx2 in range(width):
                if (self.address_space[idx + idx2]):
                    return False
            return True

        if start + width > 16:
            start = 0
            loop = False

        for idx in range(start, len(self.address_space)):
            if self.address_space[idx] == False and _checkWidth(idx):
                return idx

        if loop:
            return self._find_space(0, width, False)
        return -1
