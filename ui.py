
# pylint: disable=no-name-in-module
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QStyledItemDelegate

# pylint: disable=import-error
from lisp.ui.qdelegates import RadioButtonDelegate

class LabelDelegate(QStyledItemDelegate):
    '''Read/display-only text delegate. Y'know, a "Label".'''
    # pylint: disable=too-few-public-methods

    def createEditor(self, parent, option, index):
        # pylint: disable=invalid-name, no-self-use, unused-argument,
        '''Disable the Editor'''
        return None

class RadioButtonHidableDelegate(RadioButtonDelegate):
    '''Hidable Radio Button Delegate

    If the value of the stored data is -1, then the Delegate does not get drawn.
    Else, the Delegate gets drawn (to reflect True/False => Checked/Unchecked) as usual.
    '''
    def paint(self, painter, option, index):
        # pylint: disable=no-self-use
        if index.data(Qt.EditRole) == -1:
            return
        super().paint(painter, option, index)
