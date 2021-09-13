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

# pylint: disable=missing-docstring, invalid-name

from math import log10

# pylint: disable=no-name-in-module
from PyQt5.QtCore import QPointF, QRect, Qt
from PyQt5.QtGui import (
    QColor,
    QFontDatabase,
    QFontMetrics,
    QPainter,
)
from PyQt5.QtWidgets import QAbstractSlider, QStyle, QStyleOptionSlider

class Fader(QAbstractSlider):

    textWidth = 52
    sliderStyleOption = QStyleOptionSlider()
    sliderCurve = 128
    sliderResol = 1024
    ticks = [-60, -54, -48, -42, -36, -30, -24, -18, -12, -9, -6, -3, 0, 3, 6, 9, 10]

    def __init__(
        self,
        parent=None,
        dBMin=-60,
        dBMax=+10,
        **kwargs
    ):
        super().__init__(parent, **kwargs)

        self.dBMin = dBMin
        self.dBMax = dBMax

        self._mouseDown = False
        self._sliderMargin = 0
        self._sliderX = (0,0)

        self.borderColor = QColor(80, 80, 80)
        self.markings = []

        self.setSingleStep(1)
        self.setPageStep(3)
        self.setOrientation(Qt.Horizontal)
        self.setFocusPolicy(Qt.WheelFocus)

        font = QFontDatabase.systemFont(QFontDatabase.FixedFont)
        font.setPointSize(font.pointSize() - 4)
        self._unit_font = font

    def setupSlider(self):
        self.sliderStyleOption.initFrom(self)
        self.sliderStyleOption.rect = QRect(0, 0, self.width() - self.textWidth, 12)
        self.sliderStyleOption.minimum = self.dbToSliderValue(self.dBMin)
        self.sliderStyleOption.maximum = self.dbToSliderValue(self.dBMax)

        self._sliderMargin = self.style().subControlRect(
            QStyle.CC_Slider,
            self.sliderStyleOption,
            QStyle.SC_SliderHandle
        ).width() / 2
        self._sliderX = (
            self._sliderMargin,
            self.width() - self.textWidth - self._sliderMargin
        )

    def updateMarkings(self):
        self.markings = []
        left_coord = (self.dbToSliderValue(self.dBMin), self._sliderX[0])
        right_coord = (self.dbToSliderValue(self.dBMax), self._sliderX[1])
        for tick in self.ticks:
            self.markings.append([
                tick,
                self._linear_rescale_point(self.dbToSliderValue(tick), left_coord, right_coord),
            ])

    def dbToSliderValue(self, dbValue):
        return round((10 ** (dbValue / self.sliderCurve)) * self.sliderResol)

    def dbFromSliderValue(self, sliderValue):
        return round(self.sliderCurve * log10(sliderValue / self.sliderResol))

    def _linear_rescale_point(self, point, coord_a, coord_b):
        '''Rescales a point on one range to where it would be on another.

        The given point doesn't have to be contained within the original range.

        Sanitising the output (restricting it to 0-127, 0-1023, etc.) should be
        undertaken by the caller.
        '''
        scale = (coord_b[1] - coord_a[1]) / (coord_b[0] - coord_a[0])
        point_new = coord_a[1] + (point - coord_a[0]) * scale
        return int(point_new)

    def enterEvent(self, event):
        # pylint: disable=unused-argument
        self.sliderStyleOption.state |= QStyle.State_HasFocus

    def leaveEvent(self, event):
        # pylint: disable=unused-argument
        self.sliderStyleOption.state ^= QStyle.State_HasFocus

    def isOverSlider(self, event):
        # 0 : Not over slider
        # 1 : Over groove
        # 2 : Over handle
        return self.style().hitTestComplexControl(
            QStyle.CC_Slider,
            self.sliderStyleOption,
            event.pos(),
            self
        )

    def updatePositionFromMouse(self, xPos):
        x1 = (self._sliderX[0], self.sliderStyleOption.minimum)
        x2 = (self._sliderX[1], self.sliderStyleOption.maximum)
        point = self._linear_rescale_point(xPos, x1, x2)
        self.setValue(self.dbFromSliderValue(point))

    def mouseMoveEvent(self, event):
        if self.isSliderDown():
            self.updatePositionFromMouse(event.x())

    def mousePressEvent(self, event):
        hit = self.isOverSlider(event)
        if hit == 0:
            return

        self.setSliderDown(True)
        if hit == 1:
            self.updatePositionFromMouse(event.x())

    def mouseReleaseEvent(self, event):
        # pylint: disable=unused-argument
        if self.isSliderDown():
            self.setSliderDown(False)

    def resizeEvent(self, event):
        # pylint: disable=unused-argument
        self.setupSlider()
        self.updateMarkings()

    def paintEvent(self, event):
        super().paintEvent(event)

        height = self.height()
        width = self.width()

        painter = QPainter()
        painter.begin(self)

        # Draw markings underneath slider
        painter.setPen(self.borderColor)
        for mark in self.markings:
            painter.drawLine(
                QPointF(mark[1], 0),
                QPointF(mark[1], height)
            )

        # Write current level
        painter.setPen(self.palette().windowText().color())
        painter.drawText(
            width - self.textWidth, 0,
            self.textWidth, height,
            Qt.AlignCenter,
            str(self.value()) + " dB"
        )

        # Draw markings' texts (underneath the slider's handle)
        text_height = QFontMetrics(self._unit_font).ascent()
        painter.setFont(self._unit_font)
        for mark in self.markings:
            painter.drawText(
                mark[1] + 2,
                height - text_height,
                width,
                text_height,
                Qt.AlignLeft,
                str(mark[0]),
            )

        # Draw slider
        self.sliderStyleOption.sliderPosition = self.dbToSliderValue(self.value())
        self.sliderStyleOption.palette = self.palette()
        self.style().drawComplexControl(QStyle.CC_Slider, self.sliderStyleOption, painter)

        painter.end()
