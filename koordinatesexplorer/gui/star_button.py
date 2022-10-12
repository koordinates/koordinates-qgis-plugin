from qgis.PyQt.QtCore import (
    Qt
)
from qgis.PyQt.QtGui import (
    QPixmap
)
from qgis.PyQt.QtWidgets import (
    QLabel
)

from .gui_utils import GuiUtils
from ..api import KoordinatesClient


class StarButton(QLabel):

    def __init__(self, checked: bool, dataset_id, parent=None):
        super().__init__(parent)
        self.setMouseTracking(True)
        self._dataset_id = dataset_id
        self._checked = checked
        self._hover = False
        self._update_icon()

    def enterEvent(self, event):
        if not self._checked:
            self._hover = True
        self._update_icon()

    def leaveEvent(self, event):
        self._hover = False
        self._update_icon()

    def _update_icon(self):
        if self._checked:
            icon = GuiUtils.get_svg_as_image('star_filled.svg', 24, 24)
        elif self._hover:
            icon = GuiUtils.get_svg_as_image('star_not-starred-hover.svg', 24, 24)
        else:
            icon = GuiUtils.get_svg_as_image('star_not-starred.svg', 24, 24)

        self.setPixmap(QPixmap.fromImage(icon))

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            to_star = not self._checked
            KoordinatesClient.instance().star(self._dataset_id, is_starred=to_star)
            self._checked = to_star
            self._update_icon()
        else:
            super().mousePressEvent(event)