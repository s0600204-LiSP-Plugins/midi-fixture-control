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

import logging

# pylint: disable=no-name-in-module
from PyQt5.QtCore import QT_TRANSLATE_NOOP

from midi_fixture_library import Fixture, FixtureWidthError

# pylint: disable=import-error
from lisp.core.plugin import Plugin
from lisp.ui.settings.session_configuration import SessionConfigurationDialog

from .fixture_command_cue import FixtureCommandCue
from .midi_fixture_settings import MidiFixtureSettings

logger = logging.getLogger(__name__) # pylint: disable=invalid-name

class MidiFixtureControl(Plugin):
    """Provides the ability to control a pre-identified MIDI fixture"""

    Name = 'Midi Fixture Control'
    Authors = ('s0600204',)
    Depends = ('Midi',)
    Description = 'Provides the ability to control a pre-identified MIDI fixture'

    def __init__(self, app):
        super().__init__(app)

        # Register the settings widget
        SessionConfigurationDialog.registerSettingsPage(
            'midi_fixture_control', MidiFixtureSettings, self)

        # Register the Fixture Command cue type
        app.cue_factory.register_factory(FixtureCommandCue.__name__, FixtureCommandCue)
        app.window.registerSimpleCueMenu(
            FixtureCommandCue, QT_TRANSLATE_NOOP("CueCategory", "Integration cues")
        )

        self.fixtures = {}

    def _on_session_initialised(self):
        self._on_session_config_altered(None)

    def get_patched_output(self, patch_id):
        for patch in self.SessionConfig.get('patches'):
            if patch["patch_id"] == patch_id:
                return patch["midi_patch_id"]
        return None

    def get_profile(self, patch_id=None):
        if patch_id is None:
            if self.SessionConfig['default_patch']:
                return self.fixtures[self.SessionConfig['default_patch']]
            return None

        if patch_id not in self.fixtures:
            logger.warning('Patch ID "%s" not in prepped fixtures.', {patch_id})
            return None

        return self.fixtures[patch_id]

    def _on_session_config_altered(self, _):
        for patch in self.SessionConfig['patches']:
            patch_id = patch['patch_id']

            if patch_id not in self.fixtures:
                self.fixtures[patch_id] = Fixture(
                    patch['fixture_id'],
                    channel=patch['midi_channel'] if 'midi_channel' in patch else None,
                    deviceid=patch['midi_deviceid'] if 'midi_deviceid' in patch else None
                )
                continue

            if 'midi_deviceid' in patch and patch['midi_deviceid'] != self.fixtures[patch_id].deviceid:
                self.fixtures[patch_id].deviceid = patch['midi_deviceid']

            if 'midi_channel' in patch and (self.fixtures[patch_id].channel is None or patch['midi_channel'] < self.fixtures[patch_id].channel):
                self.fixtures[patch_id].channel = patch['midi_channel']

            if 'midi_channel' in patch:
                if patch['midi_channel'] > self.fixtures[patch_id].channel:
                    self.fixtures[patch_id].channel = patch['midi_channel']
            elif self.fixtures[patch_id].channel is not None:
                self.fixtures[patch_id].channel = None

            if 'midi_deviceid' not in patch and self.fixtures[patch_id].deviceid is not None:
                self.fixtures[patch_id].deviceid = None
