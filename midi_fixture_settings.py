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

from copy import copy

# pylint: disable=no-name-in-module
from PyQt5.QtCore import Qt, QAbstractTableModel, QModelIndex
from PyQt5.QtWidgets import QGridLayout, QGroupBox, QPushButton, QVBoxLayout

from lisp.plugins import get_plugin
from lisp.plugins.midi_fixture_control.midi_fixture_select import FixtureSelectDialog
from lisp.plugins.midi_fixture_control.ui import LabelDelegate
from lisp.ui.qdelegates import RadioButtonDelegate, SpinBoxDelegate
from lisp.ui.qviews import SimpleTableView
from lisp.ui.settings.pages import SettingsPage
from lisp.ui.ui_utils import translate

class MidiFixtureSettings(SettingsPage):
    Name = "MIDI Fixture Patch"

    TABLE_COLUMNS = [
        None,
        {
            'delegate': SpinBoxDelegate(minimum=1, maximum=16),
            'width': 72
        }, {
            'delegate': LabelDelegate(),
            'width': 28
        }, {
            'delegate': LabelDelegate()
        }, {
            'delegate': RadioButtonDelegate(),
            'width': 64
        }
    ]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.setLayout(QVBoxLayout())
        self.layout().setAlignment(Qt.AlignTop)

        self.fixtureSelectDialog = FixtureSelectDialog(parent=self)

        self.patchGroup = QGroupBox(self)
        self.patchGroup.setTitle("MIDI Fixture Patch")
        self.patchGroup.setLayout(QGridLayout())
        self.layout().addWidget(self.patchGroup)

        self.patchListModel = MidiPatchModel()
        self.patchListView = SimpleTableView(self.patchListModel, self.TABLE_COLUMNS)
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
        self.patchListModel.appendPatch(fixture_id)

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

class MidiPatchModel(QAbstractTableModel):
    '''MIDI Patch Model'''

    def __init__(self):
        super().__init__()
        self.address_space = MidiAddressSpace()
        self.rows = []
        self.columns = [
            {
                'label': 'Fixture ID',
                'flags': Qt.NoItemFlags
            }, {
                'label': translate('MidiFixtureSettings', 'MIDI #'),
                'flags': Qt.ItemIsEditable | Qt.ItemIsEnabled | Qt.ItemIsSelectable
            }, {
                'label': translate('MidiFixtureSettings', 'To'),
                'flags': Qt.ItemIsEnabled | Qt.ItemIsSelectable,
                'getter': self._get_midi_address_end
            }, {
                'label': translate('MidiFixtureSettings', 'Manufacturer & Model'),
                'flags': Qt.ItemIsEnabled | Qt.ItemIsSelectable,
                'getter': self._get_fixture_label
            }, {
                'label': translate('MidiFixtureSettings', 'Default'),
                'flags': Qt.ItemIsEditable | Qt.ItemIsUserCheckable | Qt.ItemIsEnabled | Qt.ItemIsSelectable
            }
        ]

    def rowCount(self, parent=None):
        # pylint: disable=invalid-name, missing-docstring, unused-argument
        return len(self.rows)

    def columnCount(self, parent=None):
        # pylint: disable=invalid-name, missing-docstring, unused-argument
        return len(self.columns)

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        # pylint: disable=invalid-name, missing-docstring
        if role == Qt.DisplayRole and orientation == Qt.Horizontal:
            return self.columns[section]['label']

        if role == Qt.SizeHintRole and orientation == Qt.Vertical:
            return 0

    def data(self, index, role=Qt.DisplayRole):
        if index.isValid():
            if role == Qt.DisplayRole or role == Qt.EditRole:
                if 'getter' in self.columns[index.column()]:
                    return self.columns[index.column()]['getter'](index.row())
                return self.rows[index.row()][index.column()]
            elif role == Qt.TextAlignmentRole:
                return Qt.AlignCenter
            elif role == Qt.CheckStateRole:
                if self.flags(index) & Qt.ItemIsUserCheckable:
                    return Qt.Checked if index.data(Qt.EditRole) else Qt.Unchecked
        return None

    def _get_midi_address_end(self, row):
        library = get_plugin('MidiFixtureControl').get_library()

        fixture_id = self.data(self.createIndex(row, 0))
        fixture_address = self.data(self.createIndex(row, 1))
        fixture_profile = library.get_device_profile(fixture_id)

        return fixture_profile['width'] + fixture_address - 1

    def _get_fixture_label(self, row):
        library = get_plugin('MidiFixtureControl').get_library()

        fixture_id = self.data(self.createIndex(row, 0))
        fixture_profile = library.get_device_profile(fixture_id)

        return '{manu} {model}'.format_map({
            'manu': library.get_manufacturer_list()[fixture_profile['manufacturer']],
            'model': fixture_profile['name']
        })

    def setData(self, index, value, role=Qt.DisplayRole):
        # pylint: disable=invalid-name, missing-docstring
        if index.isValid() and self.flags(index) & Qt.ItemIsEditable:
            if role == Qt.DisplayRole or role == Qt.EditRole:
                self.rows[index.row()][index.column()] = value
                self.dataChanged.emit(self.index(index.row(), 0),
                                      self.index(index.row(), index.column()),
                                      [Qt.DisplayRole, Qt.EditRole])
                return True

            if role == Qt.CheckStateRole:
                self.rows[index.row()][index.column()] = True if value is Qt.Checked else False
                self.dataChanged.emit(self.index(index.row(), 0),
                                      self.index(index.row(), index.column()),
                                      [Qt.CheckStateRole])
                return True

        return False

    def appendPatch(self, fixture_id):
        library = get_plugin('MidiFixtureControl').get_library()
        fixture_profile = library.get_device_profile(fixture_id)

        fixture_width = fixture_profile['width']
        fixture_address = self.address_space.find_block(1, fixture_width, loop=False)
        if fixture_address == -1:
            return

        self.address_space.fill_block(fixture_address, fixture_width)

        row = self.rowCount() - 1
        self.beginInsertRows(QModelIndex(), row, row)
        self.rows.append([fixture_id,
                          fixture_address,
                          None,
                          None,
                          self.rowCount() == 0])
        self.endInsertRows()

    def flags(self, index):
        return self.columns[index.column()]['flags']

class MidiAddressSpace:
    '''

    MIDI Channels 1-16 (NOT 0-15)
    '''
    def __init__(self):
        self.address_space = [False for i in range(16)]

    def fill_block(self, start, length):
        if start < 1 or start > 16 or \
            length < 1 or length > 16 or \
            start + length > 17:
            return False
        start -= 1
        working_space = copy(self.address_space)

        for idx in range(start, start + length):
            if working_space[idx]:
                return False
            working_space[idx] = True

        self.address_space = working_space
        return True

    def empty_block(self, start, length):
        if start < 1 or start > 16 or \
            length < 1 or length > 16 or \
            start + length > 17:
            return False
        start -= 1
        working_space = copy(self.address_space)

        for idx in range(start, start + length):
            if not working_space[idx]:
                return False
            working_space[idx] = False

        self.address_space = working_space
        return True

    def find_block(self, start, length, existing=False, loop=False):
        if start < 1 or start > 16 or length < 1 or length > 16:
            return -1
        start -= 1
        working_space = copy(self.address_space)

        if existing:
            ex_start = max(1, min(existing[0], 16)) - 1
            ex_end = max(1, min(existing[1] + ex_start, 16))
            for idx in range(ex_start, ex_end):
                working_space[idx] = False

        def _check_length(idx):
            for idx2 in range(length):
                if idx + idx2 > 15 or working_space[idx + idx2]:
                    return False
            return True

        if start + length > 16:
            start = 0
            loop = False

        for idx in range(start, len(self.address_space)):
            if not working_space[idx] and _check_length(idx):
                return idx + 1

        if loop:
            return self.find_block(0, length, loop=False)
        return -1
