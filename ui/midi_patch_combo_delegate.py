
from lisp.plugins.midi.widgets import MIDIPatchCombo
from lisp.ui.qdelegates import ComboBoxDelegate

class MIDIPatchComboDelegate(ComboBoxDelegate):

    def __init__(self, direction, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._direction = direction

    def createEditor(self, parent, option, index):
        editor = MIDIPatchCombo(direction=self._direction, parent=parent)
        editor.setFrame(False)
        editor.retranslateUi()
        return editor

