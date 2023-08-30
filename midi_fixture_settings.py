# This file is a derivation of work on - and as such shares the same
# licence as - Linux Show Player
#
# Linux Show Player:
#   Copyright 2012-2021 Francesco Ceruti <ceppofrancy@gmail.com>
#
# This file:
#   Copyright 2021 s0600204
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

from midi_fixture_library import Catalogue

# pylint: disable=import-error
from lisp.plugins import get_plugin
from lisp.core.plugin import PluginNotLoadedError
from lisp.plugins.midi.midi_utils import PortDirection
from lisp.ui.qdelegates import SpinBoxDelegate
from lisp.ui.settings.pages import SettingsPage
from lisp.ui.ui_utils import translate

from .midi_fixture_select import FixtureSelectDialog
from .ui import LabelDelegate, MIDIPatchComboDelegate, RadioButtonDelegate, RadioButtonHidableDelegate, SimpleTableView

logger = logging.getLogger(__name__) # pylint: disable=invalid-name

class MidiFixtureSettings(SettingsPage):
    # pylint: disable=invalid-name
    Name = "MIDI Fixture Patch"

    TABLE_COLUMNS = [
        None, None,
        {
            'delegate': MIDIPatchComboDelegate(PortDirection.Output),
            'width': 128
        }, {
            'delegate': SpinBoxDelegate(minimum=1, maximum=16),
            'width': 72
        }, {
            'delegate': LabelDelegate(),
            'width': 28
        }, {
            'delegate': SpinBoxDelegate(minimum=0, maximum=111),
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
            if not get_plugin('DcaPlotter').is_loaded():
                self.TABLE_COLUMNS[8] = None
        except PluginNotLoadedError:
            self.TABLE_COLUMNS[8] = None

        self.fixtureSelectDialog = FixtureSelectDialog(parent=self)

        self.patchGroup = QGroupBox(self)
        self.patchGroup.setTitle("MIDI Fixture Patch")
        self.patchGroup.setLayout(QGridLayout())
        self.layout().addWidget(self.patchGroup)

        self.patchListModel = MidiPatchModel()
        self.patchListView = SimpleTableView(self.patchListModel, self.TABLE_COLUMNS)
        self.patchGroup.layout().addWidget(self.patchListView, 0, 0, 1, 2)

        self.addToPatchButton = QPushButton(self.patchGroup)
        self.addToPatchButton.setText('Add')
        self.addToPatchButton.clicked.connect(self._addPatch)
        self.patchGroup.layout().addWidget(self.addToPatchButton, 1, 0)

        self.removeFromPatchButton = QPushButton(self.patchGroup)
        self.removeFromPatchButton.setText('Remove')
        self.removeFromPatchButton.clicked.connect(self._removePatch)
        self.patchGroup.layout().addWidget(self.removeFromPatchButton, 1, 1)

    def _addPatch(self):
        fixture_id = self.selectFixture()
        if not fixture_id:
            return
        self.patchListModel.appendPatch(fixture_id)

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
        self._midi = get_plugin('Midi')
        self.channel_address_spaces = {}
        self.deviceid_address_spaces = {}
        if hasattr(self._midi, "output_patches"):
            for midi_patch_id in self._midi.output_patches():
                self.channel_address_spaces[midi_patch_id] = MidiChannelAddressSpace()
                self.deviceid_address_spaces[midi_patch_id] = MidiDeviceIdAddressSpace()
        else:
            self.channel_address_spaces["out"] = MidiChannelAddressSpace()
            self.deviceid_address_spaces["out"] = MidiDeviceIdAddressSpace()

        self.catalogue = Catalogue(include_unstable=True)
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
                'id': 'midi_patch',
                'label': translate('MidiFixtureSettings', 'MIDI Output'),
                'flags': Qt.ItemIsEditable | Qt.ItemIsEnabled | Qt.ItemIsSelectable,
                'getter': self._getMidiPatchName,
                'setter': self._updateMidiPatch
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

    def _getMidiPatchName(self, row):
        midi_patch = self.data(self.getIndex(row, 'midi_patch'), Qt.EditRole)
        return self._midi.output_name_formatted(midi_patch)

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
        midi_patch = list(self.channel_address_spaces.keys())[0]

        fixture_address = -1
        if fixture_profile['requiresMidiChannel']:
            fixture_width = fixture_profile['width']
            fixture_address = self.channel_address_spaces[midi_patch].find(1, fixture_width)
            if fixture_address == -1:
                return
            self.channel_address_spaces[midi_patch].add(fixture_address, fixture_width)

        fixture_deviceid = -1
        if fixture_profile['requiresMidiDeviceID']:
            fixture_deviceid = self.deviceid_address_spaces[midi_patch].find(1)
            self.deviceid_address_spaces[midi_patch].add(fixture_deviceid)

        set_dca = True
        for r in range(self.rowCount()):
            if self.flags(self.getIndex(r, 'dca_indicator')) & Qt.ItemIsUserCheckable:
                set_dca = False
                break

        row = self.rowCount() - 1
        self.beginInsertRows(QModelIndex(), row, row)
        self.rows.append(['patch#{0}'.format(self.patch_count),
                          fixture_id,
                          midi_patch,
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

        midi_patch = self.data(self.getIndex(row, 'midi_patch'), Qt.EditRole)
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
                new_address = self.channel_address_spaces[midi_patch].find(old_address,
                                                                           new_width,
                                                                           previous=[old_address, old_width])
            else:
                new_address = self.channel_address_spaces[midi_patch].find(1, new_width)

            # If the new address is -1, there isn't space for this device
            if new_address == -1:
                logger.warning("No space for this device!")
                return

        ### MIDI Device IDs:
        # If the old profile needed a MIDI device id, but the new one doesn't: remove the assignment
        if old_profile['requiresMidiDeviceID'] and not new_profile['requiresMidiDeviceID']:
            midi_device_id = self.data(self.getIndex(row, 'midi_device_id'))
            self.deviceid_address_spaces[midi_patch].remove(midi_device_id)
            self.setData(self.getIndex(row, 'midi_device_id'),
                         -1,
                         disable_custom_setter=True)

        # If the new profile needs a MIDI device id, but the old one didn't: add an assignment
        elif not old_profile['requiresMidiDeviceID'] and new_profile['requiresMidiDeviceID']:
            midi_device_id = self.deviceid_address_spaces[midi_patch].find(1)
            if midi_device_id == -1:
                logger.warning("No space for this device!")
                return

            self.deviceid_address_spaces[midi_patch].add(midi_device_id)
            self.setData(self.getIndex(row, 'midi_device_id'),
                         midi_device_id,
                         disable_custom_setter=True)

        ### MIDI Channel Addresses (part 2):
        # At this point we know that the device fits in both channel and deviceid
        # address spaces (where applicable). We've already updated the deviceid
        # address space, so we need to update the channel address space.
        if old_profile['requiresMidiChannel']:
            self.channel_address_spaces[midi_patch].remove(old_address, old_width)

        if new_profile['requiresMidiChannel']:
            self.channel_address_spaces[midi_patch].add(new_address, new_width)
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

        midi_patch = self.data(self.getIndex(row, 'midi_patch'), Qt.EditRole)
        fixture_id = self.data(self.getIndex(row, 'fixture_id'))
        fixture_profile = self.catalogue.device_description(fixture_id)

        if fixture_profile['requiresMidiChannel']:
            self.channel_address_spaces[midi_patch].remove(self.data(self.getIndex(row, 'address')),
                                              fixture_profile['width'])

        if fixture_profile['requiresMidiDeviceID']:
            self.deviceid_address_spaces[midi_patch].remove(self.data(self.getIndex(row, 'midi_device_id')))

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
                'midi_patch': row[self.column_map['midi_patch']],
                'patch_id': row[self.column_map['patch_id']],
                'fixture_id': row[self.column_map['fixture_id']],
            }

            fixture_profile = self.catalogue.device_description(row[self.column_map['fixture_id']])
            if fixture_profile['requiresMidiChannel']:
                new_patch['midi_channel'] = row[self.column_map['address']] - 1
            if fixture_profile['requiresMidiDeviceID']:
                new_patch['midi_deviceid'] = row[self.column_map['midi_device_id']]

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
            if 'midi_patch' in patch:
                midi_patch = patch['midi_patch']
            else:
                midi_patch = list(self.channel_address_spaces.keys())[0]
            fixture_profile = self.catalogue.device_description(patch['fixture_id'])
            self.rows.append([patch['patch_id'],
                              patch['fixture_id'],
                              midi_patch,
                              patch['midi_channel'] + 1 if 'midi_channel' in patch else -1,
                              None,
                              patch['midi_deviceid'] if 'midi_deviceid' in patch else -1,
                              None,
                              patch['patch_id'] == config['default_patch'],
                              -1 if not fixture_profile['dcaCapable'] else patch['patch_id'] == config['dca_device']]) # pylint: disable=line-too-long

            if fixture_profile['requiresMidiChannel']:
                self.channel_address_spaces[midi_patch].add(patch['midi_channel'] + 1, fixture_profile['width'])
            if fixture_profile['requiresMidiDeviceID']:
                self.deviceid_address_spaces[midi_patch].add(patch['midi_deviceid'])

        self.endInsertRows()

    def _updateMidiAddress(self, row, value):
        '''Validates and updates a user-input MIDI Address'''
        old_address = self.data(self.getIndex(row, 'address'))
        new_address = value

        midi_patch = self.data(self.getIndex(row, 'midi_patch'), Qt.EditRole)
        fixture_id = self.data(self.getIndex(row, 'fixture_id'))
        fixture_profile = self.catalogue.device_description(fixture_id)
        fixture_width = fixture_profile['width']

        new_address = self.channel_address_spaces[midi_patch].find(new_address,
                                                                   fixture_width,
                                                                   previous=[old_address, fixture_width])
        if new_address == -1:
            return old_address

        self.channel_address_spaces[midi_patch].remove(old_address, fixture_width)
        self.channel_address_spaces[midi_patch].add(new_address, fixture_width)
        return new_address

    def _updateMidiDeviceId(self, row, value):
        '''Validates and updates a user-input MIDI Address'''
        midi_patch = self.data(self.getIndex(row, 'midi_patch'), Qt.EditRole)
        old_address = self.data(self.getIndex(row, 'midi_device_id'))
        new_address = self.deviceid_address_spaces[midi_patch].find(value, previous=old_address)

        if new_address == -1:
            return old_address

        self.deviceid_address_spaces[midi_patch].remove(old_address)
        self.deviceid_address_spaces[midi_patch].add(new_address)

        return new_address

    def _updateMidiPatch(self, row, value):
        old_patch = self.data(self.getIndex(row, 'midi_patch'), Qt.EditRole)
        new_patch = value
        if old_patch == new_patch:
            return old_patch

        fixture_id = self.data(self.getIndex(row, 'fixture_id'))
        fixture_profile = self.catalogue.device_description(fixture_id)

        if fixture_profile['requiresMidiChannel']:
            current_address = self.data(self.getIndex(row, 'address'))
            fixture_width = fixture_profile['width']
            new_address = self.channel_address_spaces[new_patch].find(
                current_address, fixture_width
            )
            if new_address == -1:
                logger.warning("No space in this address space!")
                return old_patch

        if fixture_profile['requiresMidiDeviceID']:
            current_deviceid = self.data(self.getIndex(row, 'midi_device_id'))
            new_deviceid = self.deviceid_address_spaces[new_patch].find(current_deviceid)
            if new_deviceid == -1:
                logger.warning("No space in this address space!")
                return old_patch

            self.deviceid_address_spaces[old_patch].remove(current_deviceid)
            self.deviceid_address_spaces[new_patch].add(new_deviceid)
            if current_deviceid != new_deviceid:
                self.setData(self.getIndex(row, 'midi_device_id'), new_deviceid, disable_custom_setter=True)

        if fixture_profile['requiresMidiChannel']:
            self.channel_address_spaces[old_patch].remove(current_address, fixture_width)
            self.channel_address_spaces[new_patch].add(new_address, fixture_width)
            if current_address != new_address:
                self.setData(self.getIndex(row, 'address'), new_address, disable_custom_setter=True)

        return new_patch

class AddressSpace:
    '''

    '''
    def __init__(self, upper_limit):
        self._upper_limit = upper_limit
        self.address_space = [False for i in range(self._upper_limit)]

    def _validate(self, start, width):
        if 1 > start > self._upper_limit:
            logger.error('Address outside of acceptable limits')
            return False

        if 1 > width > self._upper_limit:
            logger.error('Device width outside of acceptable limits')
            return False

        if start + width - 1 > self._upper_limit:
            logger.error('Device too wide to fit at this address')
            return False

        return True

    def fill(self, start, width):
        '''Fill a block in the address space'''
        if not self._validate(start, width):
            return False

        start -= 1
        working_space = copy(self.address_space)

        for idx in range(start, start + width):
            if working_space[idx]:
                logger.error('A device is already assigned at this address')
                return False
            working_space[idx] = True

        self.address_space = working_space
        return True

    def empty(self, start, width):
        '''Empty a block in the address space'''
        if not self._validate(start, width):
            return False

        start -= 1
        working_space = copy(self.address_space)

        for idx in range(start, start + width):
            if not working_space[idx]:
                logger.error('There is no device currently assigned at this address')
                return False
            working_space[idx] = False

        self.address_space = working_space
        return True

    def locate(self, start, width, previous=None):
        '''locate an appropriately sized empty block in the address space.

        Set `previous` if this is to replace an already existing block.
        '''
        if not self._validate(start, width):
            return -1

        start -= 1
        working_space = copy(self.address_space)

        if previous is not None:
            if not self._validate(previous[0], previous[1]):
                return -1
            prev_start = previous[0] - 1
            for idx in range(prev_start, prev_start + previous[1]):
                if not working_space[idx]:
                    logger.error('There is no device currently assigned at the previous address')
                    return -1
                working_space[idx] = False

        def _check_width(idx):
            for idx2 in range(width):
                if idx + idx2 > self._upper_limit - 1 or working_space[idx + idx2]:
                    return False
            return True

        for idx in range(start, len(self.address_space)):
            if not working_space[idx] and _check_width(idx):
                return idx + 1

        if start != 0:
            return self.locate(1, width, previous)
        return -1

class MidiChannelAddressSpace(AddressSpace):
    '''
    MIDI Channels 1-16 (NOT 0-15)
    '''
    def __init__(self):
        super().__init__(16)

    def add(self, address, width):
        '''Add a fixture into the address space.'''
        return self.fill(address, width)

    def remove(self, address, width):
        '''Removes a fixture from the address space.'''
        return self.empty(address, width)

    def find(self, address, width, previous=None):
        '''Find space wide enough for a fixture.'''
        return self.locate(address, width, previous)

class MidiDeviceIdAddressSpace(AddressSpace):
    '''
    MIDI Device ID 0-111
    '''
    def __init__(self):
        super().__init__(111)

    def add(self, address):
        '''Add a fixture into the address space.'''
        return self.fill(address, 1)

    def remove(self, address):
        '''Removes a fixture from the address space.'''
        return self.empty(address, 1)

    def find(self, address, previous=None):
        '''Find an empty slot for a fixture.'''
        if previous is not None:
            return self.locate(address, 1, previous=[previous, 1])
        return self.locate(address, 1)
