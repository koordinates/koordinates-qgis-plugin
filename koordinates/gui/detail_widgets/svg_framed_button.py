from typing import Optional

from qgis.PyQt.QtCore import (
    pyqtSignal,
    Qt
)
from qgis.PyQt.QtWidgets import (
    QFrame,
    QVBoxLayout,
    QHBoxLayout
)

from koordinates.gui.svg_label import SvgLabel


class SvgFramedButton(QFrame):
    """
    A fixed size button showing an SVG graphic.

    The SVG is rendered in a bordered frame.
    """
    clicked = pyqtSignal()

    def __init__(self, icon_name: str, width: int, height: int,
                 icon_width: int, icon_height: int, parent=None,
                 border_color: Optional[str] = None,
                 hover_border_color: Optional[str] = None):
        super().__init__(parent)

        self.setFixedSize(width, height)

        self.setCursor(Qt.CursorShape.PointingHandCursor)

        if hover_border_color:
            self.setMouseTracking(True)

        if border_color:
            self.setStyleSheet(
                """
            SvgFramedButton {{
                background-color: none;
                border-radius: 3px;
                border: 1px solid {};
                }}
            SvgFramedButton:hover {{ border-color: {}}}
            """.format(
                    border_color,
                    hover_border_color if hover_border_color else border_color
                )
            )

        svg_label = SvgLabel(icon_name, icon_width, icon_height)
        vl = QVBoxLayout()
        vl.setContentsMargins(0, 0, 0, 0)
        vl.addStretch()
        hl = QHBoxLayout()
        hl.setContentsMargins(0, 0, 0, 0)
        hl.addStretch()
        hl.addWidget(svg_label)
        hl.addStretch()
        vl.addLayout(hl)
        vl.addStretch()
        self.setLayout(vl)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.clicked.emit()
        else:
            super().mousePressEvent(event)
