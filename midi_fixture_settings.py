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

from PyQt5.QtCore import Qt#, QT_TRANSLATE_NOOP
from PyQt5.QtWidgets import QVBoxLayout, QFormLayout, QGroupBox, QLabel, QSpinBox, QPushButton

from lisp.plugins import get_plugin
from lisp.plugins.midi_fixture_control.midi_fixture_select import FixtureSelectDialog
from lisp.ui.settings.pages import ConfigurationPage
from lisp.ui.ui_utils import translate

class MidiFixtureSettings(ConfigurationPage):
    Name = "MIDI Fixture Control"

    def __init__(self, config, **kwargs):
        super().__init__(config, **kwargs)
        self.setLayout(QVBoxLayout())
        self.layout().setAlignment(Qt.AlignTop)

        self.fixtureSelectDialog = FixtureSelectDialog(parent=self)
        self.selectedFixtureID = ''

        self.fixtureGroup = QGroupBox(self)
        self.fixtureGroup.setTitle("Selected Fixture")
        self.fixtureGroup.setLayout(QVBoxLayout())
        self.layout().addWidget(self.fixtureGroup)

        self.fixtureManuLabel = QLabel(self.fixtureGroup)
        self.fixtureManuLabel.setAlignment(Qt.AlignCenter)
        self.fixtureManuLabel.setStyleSheet('font-weight: bold;')
        self.fixtureManuLabel.setText('-')
        self.fixtureGroup.layout().addWidget(self.fixtureManuLabel)

        self.fixtureModelLabel = QLabel(self.fixtureGroup)
        self.fixtureModelLabel.setAlignment(Qt.AlignCenter)
        self.fixtureModelLabel.setStyleSheet('font-weight: bold;')
        self.fixtureModelLabel.setText('-')
        self.fixtureGroup.layout().addWidget(self.fixtureModelLabel)

        self.fixtureSelectButton = QPushButton(self)
        self.fixtureSelectButton.setText(translate('MidiFixtureSettings', 'Change Selected Fixture')),
        self.fixtureSelectButton.clicked.connect(self.select_fixture)
        self.fixtureGroup.layout().addWidget(self.fixtureSelectButton)

        self.midiChannelLayout = QFormLayout(self.fixtureGroup)
        self.fixtureGroup.layout().addLayout(self.midiChannelLayout)

        self.midiChannelSpin = QSpinBox(self)
        self.midiChannelSpin.setRange(1, 16)
        self.midiChannelLayout.addRow(translate('MidiFixtureSettings', 'MIDI Channel'), self.midiChannelSpin)

        self.loadConfiguration()

    def select_fixture(self):
        if self.fixtureSelectDialog.exec_() == self.fixtureSelectDialog.Accepted:
            selected = self.fixtureSelectDialog.selected_fixture()
            if not selected:
                return
            self.selectedFixtureID = selected
            self._refresh_fixture()

    def _refresh_fixture(self):
            library = get_plugin('MidiFixtureControl').get_library()
            fixture = library.get_device_profile(self.selectedFixtureID)
            self.fixtureManuLabel.setText(library.get_manufacturer_list()[fixture['manufacturer']])
            self.fixtureModelLabel.setText(fixture['name'])
            self.midiChannelSpin.setRange(1, 17 - fixture['width'])

    def applySettings(self):
        self.config['midi_channel'] = self.midiChannelSpin.value()
        if self.selectedFixtureID:
            self.config['fixture_id'] = self.selectedFixtureID
        self.config.write()

    def loadConfiguration(self):
        self.midiChannelSpin.setValue(self.config['midi_channel'])
        if self.config['fixture_id']:
            self.selectedFixtureID = self.config['fixture_id'] # todo: validate
            self._refresh_fixture()
