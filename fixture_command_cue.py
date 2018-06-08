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

from PyQt5.QtCore import Qt, QT_TRANSLATE_NOOP
from PyQt5.QtWidgets import QVBoxLayout, QFormLayout, QFrame, QLabel, QComboBox, QSpinBox, QLineEdit

from lisp.core.has_properties import Property
from lisp.cues.cue import Cue
from lisp.plugins import get_plugin
from lisp.ui.settings.cue_settings import CueSettingsRegistry
from lisp.ui.settings.pages import SettingsPage
from lisp.ui.ui_utils import translate

class FixtureCommandCue(Cue):
    Name = QT_TRANSLATE_NOOP('CueName', 'Fixture Command Cue')

    fixture_command = Property()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = translate('CueName', self.Name)

    def __start__(self, fade=False):
        return False

class FixtureCommandCueSettings(SettingsPage):
    Name = QT_TRANSLATE_NOOP('SettingsPageName', 'Fixture Command Settings')

    argument_sources = {}

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        library = get_plugin('MidiFixtureControl').get_library()
        fixture_profile = self._get_fixture_profile()
        self.setLayout(QFormLayout())

        self.fixtureLabel = QLabel(self)
        self.fixtureLabel.setAlignment(Qt.AlignCenter)
        self.fixtureLabel.setStyleSheet('font-weight: bold;')
        self.fixtureLabel.setText('{manufacturer}: {model}'.format_map({
            'manufacturer': library.get_manufacturer_list()[fixture_profile['manufacturer']],
            'model': fixture_profile['name']
        }))
        self.layout().addRow('Current Fixture:', self.fixtureLabel)

        # Dropdown for command type
        self.commandCombo = QComboBox(self)
        for cmd in fixture_profile['commands']:
            self.commandCombo.addItem(cmd, cmd)
        self.commandCombo.currentIndexChanged.connect(self._select_command)
        self.layout().addRow('Command:', self.commandCombo)

        line = QFrame(self)
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        self.layout().addRow(line)

        # Command-specific arguments
        self.argument_sources = {}
        for cmd in fixture_profile['commands']:
            for arg_name, arg_definition in fixture_profile['commands'][cmd].items():
                if arg_name in self.argument_sources:
                    continue

                if arg_definition['type'] == 'numeric':
                    arg_widget = QSpinBox(self)
                elif arg_definition['type'] == 'dropdown':
                    arg_widget = QComboBox(self)
                elif arg_definition['type'] == 'textual':
                    arg_widget = QLineEdit(self)
                else:
                    logging.warning("Unrecognised argument type: {}".format(arg_definition['type']))
                    continue

                self.layout().addRow(arg_name, arg_widget)
                self.argument_sources[arg_name] = arg_widget

    def _select_command(self, index):
        current_command_data = self._get_current_command_data()

        # Hide all currently displayed argument-receiving widgets
        for arg_widget in self.argument_sources.values():
            if not arg_widget.isHidden():
                row = self.layout().takeRow(arg_widget)
                row.labelItem.widget().hide()
                arg_widget.hide()

        # Show appropriate argument-receiving widgets, and set to defaults
        for arg_name, arg_definition in current_command_data.items():
            arg_widget = self.argument_sources[arg_name]
            arg_widget.show()
            self.layout().addRow(arg_name, arg_widget)
            if isinstance(arg_widget, QSpinBox):
                if arg_widget.receivers(arg_widget.valueChanged) > 0:
                    arg_widget.valueChanged.disconnect()
                arg_widget.setRange(1, 1)

            elif isinstance(arg_widget, QComboBox):
                if arg_widget.receivers(arg_widget.currentIndexChanged) > 0:
                    arg_widget.currentIndexChanged.disconnect()
                arg_widget.clear()

            elif isinstance(arg_widget, QLineEdit):
                arg_widget.clear()

        conditional = []
        # Give argument-receiving widgets their actual values.
        # This must be done *after* setting to defaults.
        for arg_name, arg_definition in current_command_data.items():
            if 'valuesConditionalOn' in arg_definition:
                if arg_definition['valuesConditionalOn'] not in conditional:
                    conditional.append(arg_definition['valuesConditionalOn'])
                continue

            arg_widget = self.argument_sources[arg_name]
            if isinstance(arg_widget, QSpinBox):
                limit = (limit for limit in arg_definition['values'])
                arg_widget.setRange(next(limit), next(limit))

            elif isinstance(arg_widget, QComboBox):
                for option in arg_definition['values']:
                    arg_widget.addItem(option, option)

            elif isinstance(arg_widget, QLineEdit):
                continue # nothing to do here

        # Attach liste-, uh, 'slots' where necessary.
        for arg_name in conditional:
            arg_widget = self.argument_sources[arg_name]
            if isinstance(arg_widget, QSpinBox):
                arg_widget.valueChanged.connect(lambda idx: self._change_dependant_argument(arg_name))
                arg_widget.valueChanged.emit(0)

            elif isinstance(arg_widget, QComboBox):
                arg_widget.currentIndexChanged.connect(lambda idx: self._change_dependant_argument(arg_name))
                arg_widget.currentIndexChanged.emit(0)

            else:
                # Any new entries:
                #  - Disconnect liste-, uh, 'slots' above.
                logging.debug("Need a function for dealing with an input depending on a {}".format(type(arg_widget)))

    def getSettings(self):
        conf = {
            "command": self.commandCombo.currentData(),
            "args": {}
        }
        current_command_data = self._get_current_command_data()

        for arg_name, arg_definition in current_command_data.items():
            conf["args"][arg_name] = self._get_value_from_argument_widget(arg_name)

        return {'fixture_command': conf}

    def loadSettings(self, settings):
        conf = settings.get('fixture_command', {})

        # Set to a number > 0 first, so setting to 0 actually does something
        self.commandCombo.setCurrentIndex(self.commandCombo.count() - 1)
        self.commandCombo.setCurrentIndex(self.commandCombo.findData(conf['command']) if conf else 0)

        if not conf:
            return

        for arg_name, arg_value in conf['args'].items():
            if arg_name in self.argument_sources:
                arg_widget = self.argument_sources[arg_name]
                if isinstance(arg_widget, QSpinBox):
                    arg_widget.setValue(arg_value)

                elif isinstance(arg_widget, QComboBox):
                    idx = arg_widget.findData(arg_value)
                    arg_widget.setCurrentIndex(idx if idx > -1 else 0)

                elif isinstance(arg_widget, QLineEdit):
                    arg_widget.setText(arg_value)

    def _get_value_from_argument_widget(self, widget_name):
        arg_widget = self.argument_sources[widget_name]
        if isinstance(arg_widget, QSpinBox):
            return arg_widget.value()
        elif isinstance(arg_widget, QComboBox):
            return arg_widget.currentData()
        elif isinstance(arg_widget, QLineEdit):
            return arg_widget.text()
        return ""

    def _change_dependant_argument(self, transmitter_name):
        current_command_data = self._get_current_command_data()
        current_value = self._get_value_from_argument_widget(transmitter_name)

        for arg_name, arg_definition in current_command_data.items():
            if 'valuesConditionalOn' in arg_definition and arg_definition['valuesConditionalOn'] == transmitter_name:
                arg_widget = self.argument_sources[arg_name]
                if isinstance(arg_widget, QSpinBox):
                    limit = (limit for limit in arg_definition['values'][current_value])
                    self.argument_sources[arg_name].setRange(next(limit), next(limit))

                elif isinstance(arg_widget, QComboBox):
                    for option in arg_definition['values'][current_value]:
                        arg_widget.addItem(option, option)

                # todo: handle other potential cases

    def _get_fixture_profile(self):
        library = get_plugin('MidiFixtureControl').get_library()
        module_config = get_plugin('MidiFixtureControl').get_config()
        return library.get_device_profile(module_config['fixture_id'])

    def _get_current_command_data(self):
        return self._get_fixture_profile()['commands'][self.commandCombo.currentData()]

CueSettingsRegistry().add(FixtureCommandCueSettings, FixtureCommandCue)
