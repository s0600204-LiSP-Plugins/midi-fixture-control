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

from lisp.cues.cue import Cue
from lisp.ui.settings.cue_settings import CueSettingsRegistry
from lisp.ui.settings.pages import SettingsPage
from lisp.ui.ui_utils import translate

class FixtureCommandCue(Cue):
    Name = QT_TRANSLATE_NOOP('CueName', 'Fixture Command Cue')

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = translate('CueName', self.Name)

    def __start__(self, fade=False):
        return False

class FixtureCommandCueSettings(SettingsPage):
    Name = QT_TRANSLATE_NOOP('SettingsPageName', 'Fixture Command Settings')

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def getSettings(self):
        return {}

    def loadSettings(self, settings):
        pass

CueSettingsRegistry().add(FixtureCommandCueSettings, FixtureCommandCue)
