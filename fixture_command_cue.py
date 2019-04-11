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
        self._midi_out = get_plugin('Midi').output

    def __start__(self, fade=False):
        if not self.fixture_command or not self.fixture_command['patch_id']:
            return False

        plugin_config = get_plugin('MidiFixtureControl').SessionConfig

        patch_details = None
        for patch in plugin_config['patches']:
            if patch['patch_id'] == self.fixture_command['patch_id']:
                patch_details = patch
                break

        library = get_plugin('MidiFixtureControl').get_library()
        midi_messages = library.build_device_command(patch_details['fixture_id'],
                                                     patch_details['midi_channel'],
                                                     self.fixture_command['command'],
                                                     self.fixture_command['args'])

        for dict_message in midi_messages:
            self._midi_out.send_from_dict(dict_message)

        return False

class FixtureCommandCueSettings(SettingsPage):
    Name = QT_TRANSLATE_NOOP('SettingsPageName', 'Fixture Command Settings')

    argument_sources = {}

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        library = get_plugin('MidiFixtureControl').get_library()
        self.setLayout(QFormLayout())

        def _build_patch_label(patch):
            fixture_profile = library.get_device_profile(patch['fixture_id'])
            return '{manufacturer} {model} (@{channel})'.format_map({
                'manufacturer': library.get_manufacturer_list()[fixture_profile['manufacturer']],
                'model': fixture_profile['name'],
                'channel': patch['midi_channel'] + 1})

        # Dropdown of available fixture patches
        self.patchCombo = QComboBox(self)
        module_config = get_plugin('MidiFixtureControl').SessionConfig
        for patch in module_config['patches']:
            self.patchCombo.addItem(_build_patch_label(patch), patch['patch_id'])
        self.patchCombo.currentIndexChanged.connect(self._select_patch)
        self.layout().addRow('Patched Fixture:', self.patchCombo)

        # Dropdown for command type
        self.commandCombo = QComboBox(self)
        self.layout().addRow('Command:', self.commandCombo)

        # Horizontal line
        line = QFrame(self)
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        self.layout().addRow(line)

    def _select_patch(self, index):
        # Disconnect and clear command combo
        if self.commandCombo.receivers(self.commandCombo.currentIndexChanged) > 0:
            self.commandCombo.currentIndexChanged.disconnect()
        self.commandCombo.clear()

        # Get profile
        fixture_profile = self._get_fixture_profile()

        # Supply new command list
        for cmd, details in fixture_profile['commands'].items():
            self.commandCombo.addItem(details['caption'], cmd)
        self.commandCombo.currentIndexChanged.connect(self._select_command)

        # Clear arg list
        for arg_name, arg_widget in self.argument_sources.items():
            if arg_widget.isHidden():
                # If the widget has been `.takeRow`d, running `.removeRow` throws an error.
                self.layout().addRow('temp', arg_widget)
            self.layout().removeRow(arg_widget)
        
        # Supply arg sources
        self.argument_sources = {}
        for arg_name, arg_definition in fixture_profile['parameters'].items():
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

            self.argument_sources[arg_name] = arg_widget

            # Explicitly hide the widget, ready for the `.emit()` below
            arg_widget.hide()

        self.commandCombo.currentIndexChanged.emit(0)

    def _select_command(self, index):
        current_command_parameters = self._get_current_command_parameters()
        fixture_profile = self._get_fixture_profile()

        # Hide all currently displayed argument-receiving widgets
        for arg_widget in self.argument_sources.values():
            if not arg_widget.isHidden():
                row = self.layout().takeRow(arg_widget)
                row.labelItem.widget().hide()
                arg_widget.hide()

        # Show appropriate argument-receiving widgets, and set to defaults
        for arg_name in current_command_parameters:
            arg_widget = self.argument_sources[arg_name]
            arg_widget.show()
            self.layout().addRow(fixture_profile['parameters'][arg_name]['caption'], arg_widget)
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
        for arg_name, arg_definition_specific in current_command_parameters.items():
            arg_definition = fixture_profile['parameters'][arg_name]

            if 'valuesConditionalOn' in arg_definition:
                if arg_definition['valuesConditionalOn'] not in conditional:
                    conditional.append(arg_definition['valuesConditionalOn'])
                continue
            
            values = arg_definition_specific.get('values', arg_definition.get('values', []))
            arg_widget = self.argument_sources[arg_name]
            if isinstance(arg_widget, QSpinBox):
                limit = (limit for limit in values)
                arg_widget.setRange(next(limit), next(limit))

            elif isinstance(arg_widget, QComboBox):
                for option in values:
                    arg_widget.addItem(values[option], option)

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
            'patch_id': self.patchCombo.currentData(),
            "command": self.commandCombo.currentData(),
            "args": {}
        }
        current_command_parameters = self._get_current_command_parameters()

        for arg_name, arg_definition in current_command_parameters.items():
            conf["args"][arg_name] = self._get_value_from_argument_widget(arg_name)

        return {'fixture_command': conf}

    def loadSettings(self, settings):
        conf = settings.get('fixture_command', {})

        patch_id = conf['patch_id'] if conf and conf['patch_id'] else get_plugin('MidiFixtureControl').SessionConfig['default_patch']
        idx = self.patchCombo.findData(patch_id)
        self.patchCombo.setCurrentIndex(idx)
        if not idx: # If idx == 0, then the above line will not have triggered the slot.
            self.patchCombo.currentIndexChanged.emit(0)

        if not conf:
            return

        idx = self.commandCombo.findData(conf['command']) if conf['command'] else 0
        self.commandCombo.setCurrentIndex(idx)
        if not idx: # If idx == 0, then the above line will not have triggered the slot.
            self.commandCombo.currentIndexChanged.emit(0)

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
        current_command_parameters = self._get_current_command_parameters()
        current_value = self._get_value_from_argument_widget(transmitter_name)
        fixture_profile = self._get_fixture_profile()

        for arg_name, arg_definition_specific in current_command_parameters.items():
            arg_definition = fixture_profile['parameters'][arg_name]
            if 'valuesConditionalOn' in arg_definition and arg_definition['valuesConditionalOn'] == transmitter_name:
                values = arg_definition_specific.get('values', arg_definition.get('values', {}))
                arg_widget = self.argument_sources[arg_name]

                if isinstance(arg_widget, QSpinBox):
                    limit = (limit for limit in values[current_value])
                    self.argument_sources[arg_name].setRange(next(limit), next(limit))

                elif isinstance(arg_widget, QComboBox):
                    for option in values[current_value]:
                        arg_widget.addItem(option, option)

                # todo: handle other potential cases

    def _get_fixture_profile(self):
        library = get_plugin('MidiFixtureControl').get_library()
        plugin_config = get_plugin('MidiFixtureControl').SessionConfig
        patch_id = self.patchCombo.currentData() or plugin_config['default_patch']

        fixture_id = None
        for patch in plugin_config['patches']:
            if patch['patch_id'] == patch_id:
                fixture_id = patch['fixture_id']
                break

        if not fixture_id:
            return None

        return library.get_device_profile(fixture_id)

    def _get_current_command_parameters(self):
        fixture_profile = self._get_fixture_profile()
        if fixture_profile:
            return fixture_profile['commands'][self.commandCombo.currentData()]['parameters']
        return {}

CueSettingsRegistry().add(FixtureCommandCueSettings, FixtureCommandCue)
