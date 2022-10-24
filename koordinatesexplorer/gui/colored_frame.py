from qgis.PyQt.QtCore import (
    Qt,
    QRect
)
from qgis.PyQt.QtGui import (
    QPainter,
    QColor,
    QBrush
)
from qgis.PyQt.QtWidgets import QFrame


class ColoredFrame(QFrame):

    def __init__(self, parent=None):
        super().__init__(parent)

        self.color = QColor(255, 0, 0)
        self.color_height = 20

    def set_color(self, color: QColor):
        self.color = color
        self.update()

    def paintEvent(self, event):
        if not self.color.isValid():
            return

        painter = QPainter(self)
        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(self.color))
        painter.drawRect(QRect(0, 0, self.width(), self.color_height))
        painter.end()
