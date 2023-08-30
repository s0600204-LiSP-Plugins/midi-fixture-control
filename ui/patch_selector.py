
from PyQt5.QtGui import QStandardItem
from PyQt5.QtWidgets import QComboBox

from lisp.plugins import get_plugin


class PatchSelector(QComboBox):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._midi = get_plugin('Midi')
        self._plugin = get_plugin('MidiFixtureControl')

    def add_subheader(self, midi_patch_id):
        new_item = QStandardItem(self._midi.output_name_formatted(midi_patch_id))
        new_item.setEnabled(False)
        font = new_item.font()
        font.setBold(True)
        new_item.setFont(font)
        self.model().appendRow(new_item)

    def add_definition(self, definition):
        patch_id = definition['patch_id']
        profile = self._plugin.get_profile(patch_id)
        addresses = []
        if profile.channel is not None:
            addresses.append('Channel #' + str(profile.channel + 1))
        if profile.deviceid is not None:
            addresses.append('ID #' + str(profile.deviceid + 1))
        caption = '{manufacturer} {model} [{addresses}]'.format_map(
            {
                'manufacturer': profile.profile.manufacturer_name,
                'model': profile.profile.name,
                'addresses': ', '.join(addresses),
            })
        self.addItem(caption, patch_id)

    def refresh(self):
        self.clear()

        midi_patches = {}
        for definition in self._plugin.SessionConfig['patches']:
            midi_patch_id = definition['midi_patch']
            if midi_patch_id not in midi_patches:
                midi_patches[midi_patch_id] = []
            midi_patches[midi_patch_id].append(definition)

        for midi_patch_id, definitions in midi_patches.items():
            self.add_subheader(midi_patch_id)
            for definition in definitions:
                self.add_definition(definition)
