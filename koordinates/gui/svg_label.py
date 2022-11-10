from qgis.PyQt.QtCore import QSize
from qgis.PyQt.QtSvg import QSvgWidget

from .gui_utils import GuiUtils


class SvgLabel(QSvgWidget):

    def __init__(self, icon_name: str,
                 icon_width: int, icon_height: int, parent=None):
        super().__init__(parent)

        self.setFixedSize(QSize(icon_width, icon_height))
        self.load(GuiUtils.get_icon_svg(icon_name))
