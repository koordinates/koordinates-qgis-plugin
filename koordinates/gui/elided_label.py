from typing import Optional

from qgis.PyQt.QtGui import (
    QPainter,
    QFontMetrics
)
from qgis.PyQt.QtWidgets import (
    QWidget,
    QLabel
)


class ElideLabel(QLabel):
    """
    A label which automatically elides its text if it is too long to
    fit into the label
    """

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)

    def paintEvent(self, event):
        if not self.ugly_mode:
            painter = QPainter(self)
            fm = QFontMetrics(self.font())

            # subtract 2 for a little padding
            available_width = self.width() - 2
            available_height = self.height() - 2

            # gross, let's reimplement a LOT of qt internals!
            current_x = 0
            current_y = fm.height()
            words = self.text().split(' ')
            space_width = fm.width(' ')
            line_space = fm.lineSpacing()

            painter.setFont(self.font())

            word_pos = []

            for word in words:
                word_width = fm.width(word)
                current_x += word_width
                if current_x > available_width:
                    current_x = word_width
                    current_y += line_space
                    if current_y > available_height:
                        if word_pos:
                            word_pos[-1][2] = '...'
                        break
                word_pos.append([current_x - word_width, current_y, word])

                current_x += space_width

            for x, y, word in word_pos:
                painter.drawText(x, y, word)
