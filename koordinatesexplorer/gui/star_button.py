from qgis.PyQt.QtCore import (
    Qt
)
from qgis.PyQt.QtSvg import (
    QSvgWidget
)

from .gui_utils import GuiUtils
from ..api import KoordinatesClient


class StarButton(QSvgWidget):

    def __init__(self, checked: bool, dataset_id, parent=None):
        super().__init__(parent)
        self.setMouseTracking(True)
        self._dataset_id = dataset_id
        self._checked = checked
        self._hover = False
        self.setFixedSize(24, 24)
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
            icon = GuiUtils.get_icon_svg('star_starred.svg')
        elif self._hover:
            icon = GuiUtils.get_icon_svg('star_not-starred-hover.svg')
        else:
            icon = GuiUtils.get_icon_svg('star_not-starred.svg')

        self.load(icon)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            to_star = not self._checked
            KoordinatesClient.instance().star(self._dataset_id, is_starred=to_star)
            self._checked = to_star
            self._update_icon()
        else:
            super().mousePressEvent(event)
