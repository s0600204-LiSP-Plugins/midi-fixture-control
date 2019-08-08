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
import logging

# pylint: disable=no-name-in-module
from PyQt5.QtCore import Qt, QAbstractTableModel, QModelIndex
from PyQt5.QtWidgets import QGridLayout, QGroupBox, QPushButton, QVBoxLayout

from midi_fixture_library import MIDIFixtureCatalogue

# pylint: disable=import-error
from lisp.plugins import get_plugin, PluginNotLoadedError
from lisp.ui.qdelegates import SpinBoxDelegate
from lisp.ui.settings.pages import SettingsPage
from lisp.ui.ui_utils import translate

from .midi_fixture_select import FixtureSelectDialog
from .ui import LabelDelegate, RadioButtonDelegate, RadioButtonHidableDelegate, SimpleTableView

logger = logging.getLogger(__name__) # pylint: disable=invalid-name

class MidiFixtureSettings(SettingsPage):
    # pylint: disable=invalid-name
    Name = "MIDI Fixture Patch"

    TABLE_COLUMNS = [
        None, None,
        {
            'delegate': SpinBoxDelegate(minimum=1, maximum=16),
            'width': 72
        }, {
            'delegate': LabelDelegate(),
            'width': 28
        }, {
            'delegate': SpinBoxDelegate(minimum=1, maximum=111),
            'width': 72
        }, {
            'delegate': LabelDelegate()
        }, {
            'delegate': RadioButtonDelegate(),
            'width': 64
        }, {
            'delegate': RadioButtonHidableDelegate(),
            'width': 48
        }
    ]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.setLayout(QVBoxLayout())
        self.layout().setAlignment(Qt.AlignTop)

        try:
            get_plugin('DcaPlotter')
        except PluginNotLoadedError:
            self.TABLE_COLUMNS[7] = None

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
        self.addToPatchButton.clicked.connect(self._addPatch)
        self.patchGroup.layout().addWidget(self.addToPatchButton, 1, 0)

        self.editPatchButton = QPushButton(self.patchGroup)
        self.editPatchButton.setText('Edit')
        self.editPatchButton.clicked.connect(self._amendPatch)
        self.patchGroup.layout().addWidget(self.editPatchButton, 1, 1)

        self.removeFromPatchButton = QPushButton(self.patchGroup)
        self.removeFromPatchButton.setText('Remove')
        self.removeFromPatchButton.clicked.connect(self._removePatch)
        self.patchGroup.layout().addWidget(self.removeFromPatchButton, 1, 2)

    def _addPatch(self):
        fixture_id = self.selectFixture()
        if not fixture_id:
            return
        self.patchListModel.appendPatch(fixture_id)

    def _amendPatch(self):
        if not self.patchListView.selectedIndexes():
            return

        fixture_id = self.selectFixture()
        if not fixture_id:
            return

        self.patchListModel.amendPatch(self.patchListView.selectedIndexes()[0].row(),
                                       fixture_id)

    def _removePatch(self):
        if not self.patchListView.selectedIndexes():
            return
        self.patchListModel.removePatch(self.patchListView.selectedIndexes()[0].row())

    def selectFixture(self):
        if self.fixtureSelectDialog.exec_() == self.fixtureSelectDialog.Accepted:
            selected = self.fixtureSelectDialog.selected_fixture()
            if selected:
                return selected
        return False

    def getSettings(self):
        conf = {}
        for key, value in self.patchListModel.serialise().items():
            conf[key] = value
        return conf

    def loadSettings(self, settings):
        self.patchListModel.deserialise(settings)

class MidiPatchModel(QAbstractTableModel):
    # pylint: disable=invalid-name
    '''MIDI Patch Model'''

    def __init__(self):
        super().__init__()
        self.channel_address_space = MidiAddressSpace(True)
        self.deviceid_address_space = MidiAddressSpace(False)
        self.catalogue = MIDIFixtureCatalogue()
        self.patch_count = 0
        self.rows = []
        self.columns = [
            {
                'id': 'patch_id',
                'label': 'Patch ID',
                'flags': Qt.NoItemFlags,
            }, {
                'id': 'fixture_id',
                'label': 'Fixture ID',
                'flags': Qt.ItemIsEditable
            }, {
                'id': 'address',
                'label': translate('MidiFixtureSettings', 'MIDI #'),
                'flags': Qt.ItemIsEditable | Qt.ItemIsEnabled | Qt.ItemIsSelectable,
                'flags_alt': Qt.ItemIsEditable | Qt.ItemIsSelectable,
                'setter': self._updateMidiAddress
            }, {
                'id': 'address_end',
                'label': translate('MidiFixtureSettings', 'To'),
                'flags': Qt.ItemIsSelectable,
                'getter': self._getMidiAddressEnd
            }, {
                'id': 'midi_device_id',
                'label': translate('MidiFixtureSettings', 'Device ID'),
                'flags': Qt.ItemIsEditable | Qt.ItemIsEnabled | Qt.ItemIsSelectable,
                'flags_alt': Qt.ItemIsEditable | Qt.ItemIsSelectable,
                'setter': self._updateMidiDeviceId
            }, {
                'id': 'label',
                'label': translate('MidiFixtureSettings', 'Manufacturer & Model'),
                'flags': Qt.ItemIsEnabled | Qt.ItemIsSelectable,
                'getter': self._getFixtureLabel
            }, {
                'id': 'default_indicator',
                'label': translate('MidiFixtureSettings', 'Default'),
                'flags': Qt.ItemIsEditable | Qt.ItemIsUserCheckable | Qt.ItemIsEnabled | Qt.ItemIsSelectable # pylint: disable=line-too-long
            }, {
                'id': 'dca_indicator',
                'label': translate('MidiFixtureSettings', 'DCA'),
                'flags': Qt.ItemIsEditable | Qt.ItemIsUserCheckable | Qt.ItemIsEnabled | Qt.ItemIsSelectable, # pylint: disable=line-too-long
                'flags_alt': Qt.ItemIsEditable | Qt.ItemIsSelectable
            }
        ]
        self.column_map = {col_spec['id']: col_idx for col_idx, col_spec in enumerate(self.columns)}

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
        return None

    def data(self, index, role=Qt.DisplayRole):
        if index.isValid():
            if role == Qt.DisplayRole:
                if 'getter' in self.columns[index.column()]:
                    return self.columns[index.column()]['getter'](index.row())
                value = self.rows[index.row()][index.column()]
                return value if value != -1 else '-'

            if role == Qt.EditRole:
                return self.rows[index.row()][index.column()]

            if role == Qt.TextAlignmentRole:
                return Qt.AlignCenter

            if role == Qt.CheckStateRole and self.flags(index) & Qt.ItemIsUserCheckable:
                return Qt.Checked if index.data(Qt.EditRole) else Qt.Unchecked

        return None

    def getIndex(self, row, col_id):
        # pylint: disable=invalid-name
        return self.createIndex(row, self.column_map[col_id])

    def _getMidiAddressEnd(self, row):
        fixture_id = self.data(self.getIndex(row, 'fixture_id'))
        fixture_profile = self.catalogue.device_description(fixture_id)

        if not fixture_profile['requiresMidiChannel']:
            return '-'

        fixture_address = self.data(self.getIndex(row, 'address'))
        return fixture_profile['width'] + fixture_address - 1

    def _getFixtureLabel(self, row):
        fixture_id = self.data(self.getIndex(row, 'fixture_id'))
        fixture_profile = self.catalogue.device_description(fixture_id)

        return '{manu} {model}'.format_map({
            'manu': fixture_profile['manufacturer_name'],
            'model': fixture_profile['name']
        })

    def setData(self, index, value, role=Qt.DisplayRole, disable_custom_setter=False):
        # pylint: disable=invalid-name, missing-docstring
        if index.isValid() and self.flags(index) & Qt.ItemIsEditable:

            if not disable_custom_setter and 'setter' in self.columns[index.column()]:
                value = self.columns[index.column()]['setter'](index.row(), value)

            if role in (Qt.DisplayRole, Qt.EditRole):
                self.rows[index.row()][index.column()] = value
                self.dataChanged.emit(self.index(index.row(), 0),
                                      self.index(index.row(), index.column()),
                                      [Qt.DisplayRole, Qt.EditRole])
                return True

            if role == Qt.CheckStateRole and self.flags(index) & Qt.ItemIsUserCheckable:
                self.rows[index.row()][index.column()] = value == Qt.Checked
                self.dataChanged.emit(self.index(index.row(), 0),
                                      self.index(index.row(), index.column()),
                                      [Qt.CheckStateRole])

                if value == Qt.Checked:
                    for row_idx in range(0, self.rowCount()):
                        if row_idx != index.row():
                            newIndex = self.createIndex(row_idx, index.column())
                            if self.flags(newIndex) & Qt.ItemIsUserCheckable:
                                self.setData(newIndex, Qt.Unchecked, Qt.CheckStateRole)
                return True

        return False

    def appendPatch(self, fixture_id):
        fixture_profile = self.catalogue.device_description(fixture_id)

        fixture_address = -1
        if fixture_profile['requiresMidiChannel']:
            fixture_width = fixture_profile['width']
            fixture_address = self.channel_address_space.find_block(1, fixture_width, loop=False)
            if fixture_address == -1:
                return
            self.channel_address_space.fill_block(fixture_address, fixture_width)

        fixture_deviceid = -1
        if fixture_profile['requiresMidiDeviceID']:
            fixture_deviceid = self.deviceid_address_space.find_block(1, loop=False)
            self.deviceid_address_space.fill_block(fixture_deviceid)

        set_dca = True
        for r in range(self.rowCount()):
            if self.flags(self.getIndex(r, 'dca_indicator')) & Qt.ItemIsUserCheckable:
                set_dca = False
                break

        row = self.rowCount() - 1
        self.beginInsertRows(QModelIndex(), row, row)
        self.rows.append(['patch#{0}'.format(self.patch_count),
                          fixture_id,
                          fixture_address,
                          None,
                          fixture_deviceid,
                          None,
                          self.rowCount() == 0,
                          -1 if not fixture_profile['dcaCapable'] else set_dca])
        self.endInsertRows()
        self.patch_count += 1

    def amendPatch(self, row, new_id):
        if row == -1 or row >= self.rowCount():
            return

        old_id = self.data(self.getIndex(row, 'fixture_id'))
        old_profile = self.catalogue.device_description(old_id)
        new_profile = self.catalogue.device_description(new_id)

        ### MIDI Channel Addresses (part 1):
        # Get the width of the old profile, and the old address:
        if old_profile['requiresMidiChannel']:
            old_width = old_profile['width']
            old_address = self.data(self.getIndex(row, 'address'))

        # Get the width of the new profile, and find space for the device
        if new_profile['requiresMidiChannel']:
            new_width = new_profile['width']

            if old_profile['requiresMidiChannel']:
                new_address = self.channel_address_space.find_block(old_address,
                                                                    new_width,
                                                                    existing=[old_address, old_width]) # pylint: disable=line-too-long
            else:
                new_address = self.channel_address_space.find_block(1, new_width)

            # If the new address is -1, there isn't space for this device
            if new_address == -1:
                logger.warning("No space for this device!")
                return

        ### MIDI Device IDs:
        # If the old profile needed a MIDI device id, but the new one doesn't: remove the assignment
        if old_profile['requiresMidiDeviceID'] and not new_profile['requiresMidiDeviceID']:
            midi_device_id = self.data(self.getIndex(row, 'midi_device_id'))
            self.deviceid_address_space.empty_block(midi_device_id)
            self.setData(self.getIndex(row, 'midi_device_id'),
                         -1,
                         disable_custom_setter=True)

        # If the new profile needs a MIDI device id, but the old one didn't: add an assignment
        elif not old_profile['requiresMidiDeviceID'] and new_profile['requiresMidiDeviceID']:
            midi_device_id = self.deviceid_address_space.find_block(1, loop=False)
            if midi_device_id == -1:
                logger.warning("No space for this device!")
                return

            self.deviceid_address_space.fill_block(midi_device_id)
            self.setData(self.getIndex(row, 'midi_device_id'),
                         midi_device_id,
                         disable_custom_setter=True)

        ### MIDI Channel Addresses (part 2):
        # At this point we know that the device fits in both channel and deviceid
        # address spaces (where applicable). We've already updated the deviceid
        # address space, so we need to update the channel address space.
        if old_profile['requiresMidiChannel']:
            self.channel_address_space.empty_block(old_address, old_width)

        if new_profile['requiresMidiChannel']:
            self.channel_address_space.fill_block(new_address, new_width)
            self.setData(self.getIndex(row, 'address'), new_address, disable_custom_setter=True)
        else:
            self.setData(self.getIndex(row, 'address'), -1, disable_custom_setter=True)

        ### DCA Assigns
        if old_profile['dcaCapable'] != new_profile['dcaCapable']:
            if new_profile['dcaCapable']:
                set_dca = True
                for r in range(self.rowCount()):
                    if self.flags(self.getIndex(r, 'dca_indicator')) & Qt.ItemIsUserCheckable:
                        set_dca = False
                        break
            else:
                for row_idx in range(0, self.rowCount()):
                    if row_idx != row:
                        newIndex = self.getIndex(row_idx, 'dca_indicator')
                        if self.flags(newIndex) & Qt.ItemIsUserCheckable:
                            self.setData(newIndex, Qt.Checked, Qt.CheckStateRole)
                            break

            self.setData(self.getIndex(row, 'dca_indicator'),
                         set_dca if new_profile['dcaCapable'] else -1,
                         role=Qt.EditRole)

        ### And finally the Fixture ID (which identifies the device to the Fixture Library)
        self.setData(self.getIndex(row, 'fixture_id'), new_id)

    def removePatch(self, row):
        if row == -1 or row >= self.rowCount():
            return

        fixture_id = self.data(self.getIndex(row, 'fixture_id'))
        fixture_profile = self.catalogue.device_description(fixture_id)

        if fixture_profile['requiresMidiChannel']:
            self.channel_address_space.empty_block(self.data(self.getIndex(row, 'address')),
                                                   fixture_profile['width'])

        if fixture_profile['requiresMidiDeviceID']:
            self.deviceid_address_space.empty_block(self.data(self.getIndex(row, 'midi_device_id')))

        # Check if default device or chosen dca
        formerly_default = self.data(self.getIndex(row, 'default_indicator'))
        formerly_dca = self.data(self.getIndex(row, 'dca_indicator'))

        self.beginRemoveRows(QModelIndex(), row, row)
        self.rows.pop(row)
        self.endRemoveRows()

        # Set new default device and chosen DCA (if either applicable)
        # Do this after removing the row so as to not iterate through the row we're removing
        if formerly_default and self.rowCount():
            self.setData(self.getIndex(0, 'default_indicator'), Qt.Checked, Qt.CheckStateRole)

        if formerly_dca and self.rowCount():
            for row_idx in range(0, self.rowCount()):
                newIndex = self.getIndex(row_idx, 'dca_indicator')
                if self.flags(newIndex) & Qt.ItemIsUserCheckable:
                    self.setData(newIndex, Qt.Checked, Qt.CheckStateRole)
                    break

    def flags(self, index):
        if self.data(index, Qt.EditRole) == -1:
            return self.columns[index.column()]['flags_alt']
        return self.columns[index.column()]['flags']

    def serialise(self):
        '''Serialises the contained patch data, ready for saving to file.'''
        default_patch = None
        dca_device = None
        patches = []
        for row in self.rows:
            new_patch = {
                'patch_id': row[self.column_map['patch_id']],
                'fixture_id': row[self.column_map['fixture_id']],
            }

            fixture_profile = self.catalogue.device_description(row[self.column_map['fixture_id']])
            if fixture_profile['requiresMidiChannel']:
                new_patch['midi_channel'] = row[self.column_map['address']] - 1
            if fixture_profile['requiresMidiDeviceID']:
                new_patch['midi_deviceid'] = row[self.column_map['midi_device_id']] - 1

            patches.append(new_patch)

            if row[self.column_map['default_indicator']]:
                default_patch = row[self.column_map['patch_id']]
            if row[self.column_map['dca_indicator']] == 1:
                dca_device = row[self.column_map['patch_id']]

        return {
            'patches': patches,
            'default_patch': default_patch,
            'dca_device': dca_device,
            'patch_count': self.patch_count
        }

    def deserialise(self, config):
        '''De-serialises from a configuration object, restoring the saved patches.'''
        if self.rowCount():
            logger.error('Attempting to deserialise out of sequence.')
            return

        self.patch_count = config['patch_count']
        self.beginInsertRows(QModelIndex(), -1, -1)
        for patch in config['patches']:
            fixture_profile = self.catalogue.device_description(patch['fixture_id'])
            self.rows.append([patch['patch_id'],
                              patch['fixture_id'],
                              patch['midi_channel'] + 1 if 'midi_channel' in patch else -1,
                              None,
                              patch['midi_deviceid'] + 1 if 'midi_deviceid' in patch else -1,
                              None,
                              patch['patch_id'] == config['default_patch'],
                              -1 if not fixture_profile['dcaCapable'] else patch['patch_id'] == config['dca_device']]) # pylint: disable=line-too-long

            if fixture_profile['requiresMidiChannel']:
                self.channel_address_space.fill_block(patch['midi_channel'] + 1, fixture_profile['width'])
            if fixture_profile['requiresMidiDeviceID']:
                self.deviceid_address_space.fill_block(patch['midi_deviceid'] + 1)

        self.endInsertRows()

    def _updateMidiAddress(self, row, value):
        '''Validates and updates a user-input MIDI Address'''
        old_address = self.data(self.getIndex(row, 'address'))
        new_address = value

        fixture_id = self.data(self.getIndex(row, 'fixture_id'))
        fixture_profile = self.catalogue.device_description(fixture_id)
        fixture_width = fixture_profile['width']

        new_address = self.channel_address_space.find_block(new_address,
                                                            fixture_width,
                                                            existing=[old_address, fixture_width])
        if new_address == -1:
            return old_address

        self.channel_address_space.empty_block(old_address, fixture_width)
        self.channel_address_space.fill_block(new_address, fixture_width)
        return new_address

    def _updateMidiDeviceId(self, row, value):
        '''Validates and updates a user-input MIDI Address'''
        old_address = self.data(self.getIndex(row, 'midi_device_id'))
        new_address = self.deviceid_address_space.find_block(value, existing=old_address)

        if new_address == -1:
            return old_address

        self.deviceid_address_space.empty_block(old_address)
        self.deviceid_address_space.fill_block(new_address)
        return new_address


class MidiAddressSpace:
    '''

    MIDI Channels 1-16 (NOT 0-15)
    or
    MIDI Device ID 1-111
    '''
    def __init__(self, is_channel_space):
        self._upper_limit = 16 if is_channel_space else 111
        self.address_space = [False for i in range(self._upper_limit)]

    def fill_block(self, start, length=1):
        if start < 1 or start > self._upper_limit or \
            length < 1 or length > self._upper_limit or \
            start + length > self._upper_limit + 1:
            return False
        start -= 1
        working_space = copy(self.address_space)

        for idx in range(start, start + length):
            if working_space[idx]:
                return False
            working_space[idx] = True

        self.address_space = working_space
        return True

    def empty_block(self, start, length=1):
        if start < 1 or start > self._upper_limit or \
            length < 1 or length > self._upper_limit or \
            start + length > self._upper_limit + 1:
            return False
        start -= 1
        working_space = copy(self.address_space)

        for idx in range(start, start + length):
            if not working_space[idx]:
                return False
            working_space[idx] = False

        self.address_space = working_space
        return True

    def find_block(self, start, length=1, existing=False, loop=False):
        if start < 1 or start > self._upper_limit or length < 1 or length > self._upper_limit:
            return -1
        start -= 1
        working_space = copy(self.address_space)

        if existing:
            if isinstance(existing, list):
                ex_start = max(1, min(existing[0], self._upper_limit)) - 1
                ex_end = max(1, min(existing[1] + ex_start, self._upper_limit))
                for idx in range(ex_start, ex_end):
                    working_space[idx] = False
            else:
                working_space[existing - 1] = False

        def _check_length(idx):
            for idx2 in range(length):
                if idx + idx2 > self._upper_limit - 1 or working_space[idx + idx2]:
                    return False
            return True

        if start + length > self._upper_limit:
            start = 0
            loop = False

        for idx in range(start, len(self.address_space)):
            if not working_space[idx] and _check_length(idx):
                return idx + 1

        if loop:
            return self.find_block(0, length, loop=False)
        return -1
