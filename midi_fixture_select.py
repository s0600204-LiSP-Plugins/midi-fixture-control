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

# pylint: disable=no-name-in-module
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QDialog, QGridLayout, QVBoxLayout, QFormLayout, QGroupBox, QComboBox, \
    QTreeWidget, QTreeWidgetItem, QDialogButtonBox, QHeaderView

from midi_fixture_library import Catalogue

# pylint: disable=import-error
from lisp.ui.ui_utils import translate

class FixtureSelectDialog(QDialog):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.setWindowTitle(translate('MidiFixtureSettings', 'MIDI Fixture Selection'))
        self.setMinimumSize(600, 400)
        self.catalogue = Catalogue(include_unstable=False)

        self.setLayout(QGridLayout())

        self.manufacturer_group = QGroupBox(self)
        self.manufacturer_group.setTitle(translate("MidiFixtureSettings", "Manufacturer"))
        self.manufacturer_group.setLayout(QVBoxLayout())
        self.manufacturer_group.layout().setAlignment(Qt.AlignTop)
        self.layout().addWidget(self.manufacturer_group, 0, 0)

        self.type_group = QGroupBox(self)
        self.type_group.setTitle(translate("MidiFixtureSettings", "Fixture Type"))
        self.type_group.setLayout(QFormLayout())
        self.layout().addWidget(self.type_group, 0, 1)

        self.type_manufacturer_combo = QComboBox(self)
        manu_list = self.catalogue.manufacturers()
        self.type_manufacturer_combo.addItem("(None)", None)
        for manu_id in manu_list:
            self.type_manufacturer_combo.addItem(manu_list[manu_id], manu_id)
        self.type_manufacturer_combo.currentIndexChanged.connect(self._update_list)
        self.manufacturer_group.layout().addWidget(self.type_manufacturer_combo)

        self.maintype_combo = QComboBox(self)
        type_list = self.catalogue.device_types()
        self.maintype_combo.addItem("(None)", None)
        for type_id in type_list:
            self.maintype_combo.addItem(type_list[type_id], type_id)
        self.maintype_combo.currentIndexChanged.connect(self._select_type)
        self.type_group.layout().addRow(translate('MidiFixtureSettings', 'Type'),
                                        self.maintype_combo)

        self.subtype_combo = QComboBox(self)
        self.subtype_combo.addItem("(None)", None)
        self.subtype_combo.setEnabled(False)
        self.type_group.layout().addRow(translate('MidiFixtureSettings', 'Sub-Type'),
                                        self.subtype_combo)

        self.fixture_list = QTreeWidget(self)
        self.fixture_list.setHeaderLabels(["Manufacturer", "Type", "Subtype", "Model"])
        self.fixture_list.header().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.fixture_list.setIndentation(0)
        self.layout().addWidget(self.fixture_list, 1, 0, 1, 2)

        self.buttons = QDialogButtonBox(self)
        self.buttons.addButton(QDialogButtonBox.Cancel)
        self.buttons.addButton(QDialogButtonBox.Ok)
        self.layout().addWidget(self.buttons, 2, 0, 1, 2)

        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)
        self._update_list()

    def selected_fixture(self):
        items = self.fixture_list.selectedItems()
        return items[0].data(0, Qt.UserRole) if items else None

    def _update_list(self):
        self.fixture_list.clear()

        device_list = self.catalogue.devices(self.type_manufacturer_combo.currentData(),
                                             self.maintype_combo.currentData(),
                                             self.subtype_combo.currentData())
        for device_id in device_list:
            item = QTreeWidgetItem()
            item.setData(0, Qt.UserRole, device_id)
            item.setText(0, device_list[device_id]['manufacturer_name'])
            item.setText(1, device_list[device_id]['type'])
            item.setText(2, device_list[device_id]['subtype'])
            item.setText(3, device_list[device_id]['name'])
            self.fixture_list.addTopLevelItem(item)

    def _select_type(self):
        selected_type = self.maintype_combo.currentData()

        # clear
        if self.subtype_combo.receivers(self.subtype_combo.currentIndexChanged) > 0:
            self.subtype_combo.currentIndexChanged.disconnect()
        self.subtype_combo.clear()
        self.subtype_combo.addItem("(None)", None)

        # populate
        if selected_type:
            subtype_list = self.catalogue.device_types(selected_type)
            for subtype_id in subtype_list:
                self.subtype_combo.addItem(subtype_list[subtype_id], subtype_id)
            self.subtype_combo.currentIndexChanged.connect(self._update_list)

        self.subtype_combo.setEnabled(bool(selected_type))
        self._update_list()
