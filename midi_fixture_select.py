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

from midi_fixture_library import MIDIFixtureCatalogue

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QDialog, QGridLayout, QVBoxLayout, QFormLayout, QGroupBox, QComboBox, QTreeWidget, QTreeWidgetItem, QDialogButtonBox, QHeaderView

from lisp.ui.ui_utils import translate

class FixtureSelectDialog(QDialog):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.setWindowTitle(translate('MidiFixtureSettings', 'MIDI Fixture Selection'))
        self.setMinimumSize(600, 400)
        self.catalogue = MIDIFixtureCatalogue()

        self.setLayout(QGridLayout())

        self.manufacturerGroup = QGroupBox(self)
        self.manufacturerGroup.setTitle(translate("MidiFixtureSettings", "Manufacturer"))
        self.manufacturerGroup.setLayout(QVBoxLayout())
        self.manufacturerGroup.layout().setAlignment(Qt.AlignTop)
        self.layout().addWidget(self.manufacturerGroup, 0, 0)

        self.typeGroup = QGroupBox(self)
        self.typeGroup.setTitle(translate("MidiFixtureSettings", "Fixture Type"))
        self.typeGroup.setLayout(QFormLayout())
        self.layout().addWidget(self.typeGroup, 0, 1)

        self.manufacturerCombo = QComboBox(self)
        manuList = self.catalogue.get_manufacturer_list()
        self.manufacturerCombo.addItem("(None)", None)
        for manuID in manuList:
            self.manufacturerCombo.addItem(manuList[manuID], manuID)
        self.manufacturerCombo.currentIndexChanged.connect(self._update_list)
        self.manufacturerGroup.layout().addWidget(self.manufacturerCombo)

        self.mainTypeCombo = QComboBox(self)
        typeList = self.catalogue.get_device_type_list()
        self.mainTypeCombo.addItem("(None)", None)
        for typeID in typeList:
            self.mainTypeCombo.addItem(typeList[typeID], typeID)
        self.mainTypeCombo.currentIndexChanged.connect(self._select_type)
        self.typeGroup.layout().addRow(translate('MidiFixtureSettings', 'Type'), self.mainTypeCombo)

        self.subTypeCombo = QComboBox(self)
        self.subTypeCombo.addItem("(None)", None)
        self.subTypeCombo.setEnabled(False)
        self.typeGroup.layout().addRow(translate('MidiFixtureSettings', 'Sub-Type'), self.subTypeCombo)

        self.fixtureList = QTreeWidget(self)
        self.fixtureList.setHeaderLabels(["Manufacturer", "Type", "Subtype", "Model"])
        self.fixtureList.header().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.fixtureList.setIndentation(0)
        self.layout().addWidget(self.fixtureList, 1, 0, 1, 2)

        self.buttons = QDialogButtonBox(self)
        self.buttons.addButton(QDialogButtonBox.Cancel)
        self.buttons.addButton(QDialogButtonBox.Ok)
        self.layout().addWidget(self.buttons, 2, 0, 1, 2)

        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)
        self._update_list()

    def selected_fixture(self):
        items = self.fixtureList.selectedItems()
        return items[0].data(0, Qt.UserRole) if items else None

    def _update_list(self):
        self.fixtureList.clear()

        deviceList = self.catalogue.get_device_list(self.manufacturerCombo.currentData(),
                                                    self.mainTypeCombo.currentData(),
                                                    self.subTypeCombo.currentData())
        for deviceID in deviceList:
            item = QTreeWidgetItem()
            item.setData(0, Qt.UserRole, deviceID)
            item.setText(0, deviceList[deviceID]['manufacturer_name'])
            item.setText(1, deviceList[deviceID]['type'])
            item.setText(2, deviceList[deviceID]['subtype'])
            item.setText(3, deviceList[deviceID]['name'])
            self.fixtureList.addTopLevelItem(item)

    def _select_type(self):
        fType = self.mainTypeCombo.currentData()

        # clear
        if self.subTypeCombo.receivers(self.subTypeCombo.currentIndexChanged) > 0:
            self.subTypeCombo.currentIndexChanged.disconnect()
        self.subTypeCombo.clear()
        self.subTypeCombo.addItem("(None)", None)

        # populate
        if fType:
            subTypeList = self.catalogue.get_device_type_list(fType)
            for subTypeID in subTypeList:
                self.subTypeCombo.addItem(subTypeList[subTypeID], subTypeID)
            self.subTypeCombo.currentIndexChanged.connect(self._update_list)

        self.subTypeCombo.setEnabled(bool(fType))
        self._update_list()

