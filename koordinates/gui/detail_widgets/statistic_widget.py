import platform

from qgis.PyQt.QtWidgets import (
    QWidget,
    QGridLayout,
    QLabel
)

from koordinates.gui.gui_utils import FONT_FAMILIES
from koordinates.gui.svg_label import SvgLabel


class StatisticWidget(QWidget):
    """
    A simple widget showing a key/value layout for displaying dataset
    statistics
    """

    def __init__(self, title: str, icon_name: str, value: str, parent=None):
        super().__init__(parent)

        gl = QGridLayout()
        gl.setContentsMargins(0, 0, 0, 0)

        font_size = 9
        if platform.system() == 'Darwin':
            font_size = 11

        title_label = QLabel(
            '<b style="font-family: {}; font-size: {}pt">{}</b>'.format(
                FONT_FAMILIES,
                font_size,
                title))
        gl.addWidget(title_label, 0, 0, 1, 2)

        icon = SvgLabel(icon_name, 16, 16)
        gl.addWidget(icon, 1, 0, 1, 1)

        value_label = QLabel(
            '<span style="font-family: {}; font-size: {}pt">{}</span>'.format(
                FONT_FAMILIES,
                font_size, value))
        gl.addWidget(value_label, 1, 1, 1, 1)

        self.setLayout(gl)
