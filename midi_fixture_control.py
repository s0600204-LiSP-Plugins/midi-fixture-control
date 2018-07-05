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

from midi_fixture_library import MIDIFixtureLibrary

from lisp.core.plugin import Plugin
from lisp.plugins.midi_fixture_control.fixture_command_cue import FixtureCommandCue
from lisp.plugins.midi_fixture_control.midi_fixture_settings import MidiFixtureSettings
from lisp.ui.settings.session_configuration import SessionConfigurationDialog
from lisp.ui.ui_utils import translate

class MidiFixtureControl(Plugin):
    """Provides the ability to control a pre-identified MIDI fixture"""

    Name = 'Midi Fixture Control'
    Authors = ('s0600204',)
    Depends = ('Midi',)
    Description = 'Provides the ability to control a pre-identified MIDI fixture'

    library_reference = None

    def __init__(self, app):
        super().__init__(app)
        self.library_reference = MIDIFixtureLibrary()

        # Register the settings widget
        SessionConfigurationDialog.registerSettingsPage(
            'midi_fixture_control', MidiFixtureSettings, self)

        # Register the Fixture Command cue type
        app.register_cue_type(FixtureCommandCue)

    def attach_session_config(self):
        print(self.SessionConfig)

    def get_library(self):
        return self.library_reference
