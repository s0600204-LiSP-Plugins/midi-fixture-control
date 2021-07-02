
# pylint: disable=no-name-in-module
from PyQt5.QtWidgets import QStyledItemDelegate

class LabelDelegate(QStyledItemDelegate):
    '''Read/display-only text delegate. Y'know, a "Label".'''
    # pylint: disable=too-few-public-methods

    def createEditor(self, parent, option, index):
        # pylint: disable=invalid-name, no-self-use, unused-argument,
        '''Disable the Editor'''
        return None
