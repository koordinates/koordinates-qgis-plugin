from typing import Optional

from qgis.PyQt.QtCore import Qt
from qgis.PyQt.QtGui import (
    QPainter,
    QBrush,
    QColor
)
from qgis.PyQt.QtWidgets import (
    QWidget,
    QStyleOption,
    QStylePainter
)


class RoundedHighlightBox(QWidget):
    """
    Custom widget for showing a rounded highlight box.

    NOTE: By default this widget has no layout -- that's up to callers
    to create!
    """

    CORNER_RADIUS = 4

    def __init__(self, parent: Optional[QWidget]=None):
        super().__init__(parent)

    def paintEvent(self, event):
        option = QStyleOption()
        option.initFrom(self)

        painter = QStylePainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)

        painter.save()
        brush = QBrush(QColor(0, 0, 0, 38))
        painter.setBrush(brush)
        painter.setPen(Qt.NoPen)

        painter.drawRoundedRect(option.rect,
                                    self.CORNER_RADIUS,
                                    self.CORNER_RADIUS)
        painter.restore()
