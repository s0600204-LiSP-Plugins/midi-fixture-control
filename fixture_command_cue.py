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

# pylint: disable=missing-docstring

import logging

# pylint: disable=no-name-in-module
from PyQt5.QtCore import Qt, QT_TRANSLATE_NOOP
from PyQt5.QtWidgets import QFormLayout, QFrame, QComboBox, QSlider, QSpinBox, QLineEdit

# pylint: disable=import-error
from lisp.core.has_properties import Property
from lisp.cues.cue import Cue
from lisp.plugins import get_plugin
from lisp.plugins.midi.midi_utils import midi_from_dict
from lisp.ui.settings.cue_settings import CueSettingsRegistry
from lisp.ui.settings.pages import SettingsPage
from lisp.ui.ui_utils import translate
from lisp.ui.widgets import QStyledSlider

class FixtureCommandCue(Cue):
    Name = QT_TRANSLATE_NOOP('CueName', 'Fixture Command Cue')

    fixture_command = Property()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = translate('CueName', self.Name)
        self._midi_out = get_plugin('Midi').output

    def __start__(self, _):
        if not self.fixture_command or not self.fixture_command['patch_id']:
            return False

        profile = get_plugin('MidiFixtureControl').get_profile(self.fixture_command['patch_id'])
        midi_messages = profile.build_command(self.fixture_command['command'],
                                              self.fixture_command['args'])

        for dict_message in midi_messages:
            self._midi_out.send(midi_from_dict(dict_message))

        return False

class FixtureCommandCueSettings(SettingsPage):
    Name = QT_TRANSLATE_NOOP('SettingsPageName', 'Fixture Command Settings')

    argument_sources = {}

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.setLayout(QFormLayout())

        def _build_patch_label(profile):
            addresses = []
            if profile.channel is not None:
                addresses.append('Channel #' + str(profile.channel + 1))
            if profile.deviceid is not None:
                addresses.append('ID #' + str(profile.deviceid + 1))
            return '{manufacturer} {model} [{addresses}]'.format_map(
                {
                    'manufacturer': profile.profile.manufacturer_name,
                    'model': profile.profile.name,
                    'addresses': ', '.join(addresses)
                })

        # Dropdown of available fixture patches
        self.patch_combo = QComboBox(self)
        plugin = get_plugin('MidiFixtureControl')
        for patch_definition in plugin.SessionConfig['patches']:
            patch_id = patch_definition['patch_id']
            self.patch_combo.addItem(_build_patch_label(plugin.get_profile(patch_id)), patch_id)
        self.patch_combo.currentIndexChanged.connect(self._select_patch)
        self.layout().addRow('Patched Fixture:', self.patch_combo)

        # Dropdown for command type
        self.command_combo = QComboBox(self)
        self.layout().addRow('Command:', self.command_combo)

        # Horizontal line
        line = QFrame(self)
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        self.layout().addRow(line)

    def _select_patch(self, _):
        # Disconnect and clear command combo
        if self.command_combo.receivers(self.command_combo.currentIndexChanged) > 0:
            self.command_combo.currentIndexChanged.disconnect()
        self.command_combo.clear()

        # Get profile
        fixture_profile = self._get_current_fixture_profile()

        # Supply new command list
        for cmd in fixture_profile.command_list:
            details = fixture_profile.command(cmd)
            self.command_combo.addItem(details['caption'] if 'caption' in details else cmd, cmd)
        self.command_combo.currentIndexChanged.connect(self._select_command)

        # Clear arg list
        for name, widget in self.argument_sources.items():
            if widget.isHidden():
                # If the widget has been `.takeRow`d, running `.removeRow` throws an error.
                self.layout().addRow('temp', widget)
            self.layout().removeRow(widget)

        # Supply arg sources
        self.argument_sources = {}
        for name, definition in fixture_profile.parameters().items():
            if name in self.argument_sources:
                continue

            if definition['type'] == 'numeric':
                widget = QSpinBox(self)
            elif definition['type'] == 'dropdown':
                widget = QComboBox(self)
            elif definition['type'] == 'textual':
                widget = QLineEdit(self)
            elif definition['type'] == 'slider':
                widget = QStyledSlider(self)
            else:
                logging.warning("Unrecognised argument type: %s", {definition['type']})
                continue

            self.argument_sources[name] = widget

            # Explicitly hide the widget, ready for the `.emit()` below
            widget.hide()

        self.command_combo.currentIndexChanged.emit(0)

    def _select_command(self, _):
        fixture_profile = self._get_current_fixture_profile()
        parameter_definitions = fixture_profile.parameters()
        parameter_list = self._get_current_parameter_list()

        # Hide all currently displayed argument-receiving widgets
        for widget in self.argument_sources.values():
            if not widget.isHidden():
                row = self.layout().takeRow(widget)
                row.labelItem.widget().hide()
                widget.hide()

        # Show appropriate widgets, and set to defaults
        for name in parameter_list:
            widget = self.argument_sources[name]
            widget.show()
            self.layout().addRow(parameter_definitions[name]['caption'], widget)

            if isinstance(widget, QSpinBox):
                if widget.receivers(widget.valueChanged) > 0:
                    widget.valueChanged.disconnect()
                widget.setRange(1, 1)

            elif isinstance(widget, QComboBox):
                if widget.receivers(widget.currentIndexChanged) > 0:
                    widget.currentIndexChanged.disconnect()
                widget.clear()

            elif isinstance(widget, QLineEdit):
                widget.clear()

            elif isinstance(widget, QStyledSlider):
                if widget.receivers(widget.valueChanged) > 0:
                    widget.valueChanged.disconnect()
                widget.setSingleStep(3)
                widget.setPageStep(12)
                widget.setTickPosition(QSlider.TicksBelow)
                widget.setTickInterval(10)
                widget.setOrientation(Qt.Horizontal)
                widget.setRange(1,1)

        conditional = []
        # Give input widgets their actual value ranges.
        # This must be done *after* setting to defaults.
        for name, values in parameter_list.items():
            definition = parameter_definitions[name]

            if 'valuesConditionalOn' in definition:
                if definition['valuesConditionalOn'] not in conditional:
                    conditional.append(definition['valuesConditionalOn'])
                continue

            widget = self.argument_sources[name]
            if isinstance(widget, QSpinBox) or isinstance(widget, QStyledSlider):
                limit = (limit for limit in values)
                widget.setRange(next(limit), next(limit))

            elif isinstance(widget, QComboBox):
                for option in values:
                    widget.addItem(values[option], option)

            elif isinstance(widget, QLineEdit):
                continue # nothing to do here

        # Attach liste-, uh, 'slots' where necessary.
        for name in conditional:
            widget = self.argument_sources[name]
            if isinstance(widget, QSpinBox):
                widget.valueChanged.connect(
                    lambda idx: self._change_dependant_argument(name))
                widget.valueChanged.emit(0)

            elif isinstance(widget, QComboBox):
                widget.currentIndexChanged.connect(
                    lambda idx: self._change_dependant_argument(name))
                widget.currentIndexChanged.emit(0)

            else:
                # Any new entries:
                #  - Disconnect liste-, uh, 'slots' above.
                logging.debug(
                    "Need a function for dealing with an input depending on a %s",
                    {type(widget)}
                )

    # pylint: disable=invalid-name
    def getSettings(self):
        conf = {
            'patch_id': self.patch_combo.currentData(),
            "command": self.command_combo.currentData(),
            "args": {}
        }
        parameter_list = self._get_current_parameter_list()

        for name in parameter_list.keys():
            conf["args"][name] = self._get_value_from_argument_widget(name)

        return {'fixture_command': conf}

    # pylint: disable=invalid-name
    def loadSettings(self, settings):
        conf = settings.get('fixture_command', {})

        if conf and conf['patch_id']:
            patch_id = conf['patch_id']
        else:
            patch_id = get_plugin('MidiFixtureControl').SessionConfig['default_patch']
        idx = self.patch_combo.findData(patch_id)
        self.patch_combo.setCurrentIndex(idx)
        if not idx: # If idx == 0, then the above line will not have triggered the slot.
            self.patch_combo.currentIndexChanged.emit(0)

        if not conf:
            return

        idx = self.command_combo.findData(conf['command']) if conf['command'] else 0
        self.command_combo.setCurrentIndex(idx)
        if not idx: # If idx == 0, then the above line will not have triggered the slot.
            self.command_combo.currentIndexChanged.emit(0)

        for name, value in conf['args'].items():
            if name in self.argument_sources:
                widget = self.argument_sources[name]
                if isinstance(widget, QSpinBox) or isinstance(widget, QStyledSlider):
                    widget.setValue(value)

                elif isinstance(widget, QComboBox):
                    idx = widget.findData(value)
                    widget.setCurrentIndex(idx if idx > -1 else 0)

                elif isinstance(widget, QLineEdit):
                    widget.setText(value)

    def _get_value_from_argument_widget(self, widget_name):
        widget = self.argument_sources[widget_name]
        if isinstance(widget, QSpinBox) or isinstance(widget, QStyledSlider):
            return widget.value()
        if isinstance(widget, QComboBox):
            return widget.currentData()
        if isinstance(widget, QLineEdit):
            return widget.text()
        return ""

    def _change_dependant_argument(self, transmitter_name):
        fixture_profile = self._get_current_fixture_profile()
        parameter_definitions = fixture_profile.parameters()
        parameter_list = self._get_current_parameter_list()
        current_value = self._get_value_from_argument_widget(transmitter_name)

        for name, values in parameter_list.items():
            definition = parameter_definitions[name]
            if ('valuesConditionalOn' in definition
                    and definition['valuesConditionalOn'] == transmitter_name):
                widget = self.argument_sources[name]

                if isinstance(widget, QSpinBox) or isinstance(widget, QStyledSlider):
                    limit = (limit for limit in values[current_value])
                    self.argument_sources[name].setRange(next(limit), next(limit))

                elif isinstance(widget, QComboBox):
                    for option in values[current_value]:
                        widget.addItem(option, option)

                # @todo: handle other potential cases

    def _get_current_fixture_profile(self):
        return get_plugin('MidiFixtureControl').get_profile(self.patch_combo.currentData())

    def _get_current_parameter_list(self):
        fixture_profile = self._get_current_fixture_profile()
        if fixture_profile:
            return fixture_profile.parameter_values(self.command_combo.currentData())
        return {}

CueSettingsRegistry().add(FixtureCommandCueSettings, FixtureCommandCue)
