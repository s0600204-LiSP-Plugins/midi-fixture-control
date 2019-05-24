
# pylint: disable=no-name-in-module
from PyQt5.QtCore import Qt, QEvent, QModelIndex
from PyQt5.QtGui import QMouseEvent
from PyQt5.QtWidgets import QApplication, QStyle, QStyledItemDelegate, QStyleOptionButton

class LabelDelegate(QStyledItemDelegate):
    '''Read/display-only text delegate. Y'know, a "Label".'''
    # pylint: disable=too-few-public-methods

    def createEditor(self, parent, option, index):
        # pylint: disable=invalid-name, no-self-use, unused-argument,
        '''Disable the Editor'''
        return None

class RadioButtonDelegate(QStyledItemDelegate):
    '''Radio Button Delegate

    Draws a RadioButton circle in the middle of the draw-space.

    When clicked, the state of the delegate toggles between "checked" and "unchecked".

    Logic is loosely adapted from:
      https://stackoverflow.com/questions/16237708/align-checkable-items-in-qtablewidget/16301316#16301316
    '''

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.last_clicked_index = QModelIndex()

    def createEditor(self, parent, option, index):
        # pylint: disable=invalid-name, no-self-use, unused-argument,
        '''Do not create an Editor (on double-click)'''
        return None

    def editorEvent(self, event, model, option, index):
        # pylint: disable=invalid-name
        '''Toggle checked/unchecked on mouse click'''
        if event.type() == QEvent.MouseButtonPress:
            self.last_clicked_index = index

        elif event.type() == QEvent.MouseButtonRelease:

            if index.row() is not self.last_clicked_index.row() or \
               index.column() is not self.last_clicked_index.column():
                return False

            e = QMouseEvent(event)
            if int(e.button()) is not int(Qt.LeftButton):
                return False

            self.last_clicked_index = QModelIndex()

            if index.data(Qt.CheckStateRole) is Qt.Checked:
                return False

            model.setData(index, Qt.Checked, Qt.CheckStateRole)
            return True

        return super().editorEvent(event, model, option, index)

    def paint(self, painter, option, index):
        # pylint: disable=no-self-use
        '''Draw a radio-button circle in the middle of the draw-space'''

        button_option = QStyleOptionButton()
        button_option.state |= QStyle.State_On if index.data(Qt.CheckStateRole) == Qt.Checked else QStyle.State_Off
        button_option.rect = QApplication.style().subElementRect(QStyle.SE_RadioButtonIndicator,
                                                                 option)
        button_option.rect.moveTo(option.rect.center().x() - button_option.rect.width() / 2,
                                  option.rect.center().y() - button_option.rect.height() / 2)

        QApplication.style().drawPrimitive(QStyle.PE_IndicatorRadioButton, button_option, painter)

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
