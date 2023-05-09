import platform
from typing import (
    List,
    Tuple
)

from qgis.PyQt.QtCore import (
    Qt,
)
from qgis.PyQt.QtGui import (
    QFontMetrics,
    QFont
)
from qgis.PyQt.QtWidgets import (
    QGridLayout,
    QLabel
)

from .horizontal_line_widget import HorizontalLine
from ..gui_utils import (
    FONT_FAMILIES,
    MONOSPACE_FONT_FAMILIES
)


class DetailsTable(QGridLayout):
    """
    A table widget for showing datasets details
    """

    def __init__(self, title: str, parent=None):
        super().__init__(parent)
        self.setVerticalSpacing(13)
        self.font_size = 10
        if platform.system() == 'Darwin':
            self.font_size = 14

        heading = QLabel(
            """<b style="font-family: {};""".format(FONT_FAMILIES) +
            """font-size: {}pt;""".format(self.font_size) +
            """color: black">{}</b>""".format(title))
        self.addWidget(heading, 0, 0, 1, 2)
        self.setColumnStretch(1, 1)

    def push_row(self, title: str, value: str):
        if self.rowCount() > 1:
            self.addWidget(HorizontalLine(), self.rowCount(), 0, 1, 2)

        is_monospace = title.startswith('_')
        if is_monospace:
            title = title[1:]

        row = self.rowCount()
        title_label = QLabel(
            """<span style="font-family: {};
            font-size: {}pt;
            color: #868889">{}</span>""".format(FONT_FAMILIES,
                                                self.font_size,
                                                title))
        title_label.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextBrowserInteraction)
        title_label.setOpenExternalLinks(True)

        fm = QFontMetrics(QFont())
        title_label.setFixedWidth(fm.width('x') * 30)
        title_label.setAlignment(
            Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        self.addWidget(title_label, row, 0, 1, 1)
        font_family = FONT_FAMILIES if not is_monospace \
            else MONOSPACE_FONT_FAMILIES
        value_label = QLabel(
            """<span style="font-family: {};""".format(font_family) +
            """font-size: {}pt;""".format(self.font_size) +
            """color: black">{}</span>""".format(value))
        value_label.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextBrowserInteraction)
        value_label.setOpenExternalLinks(True)
        value_label.setAlignment(
            Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        value_label.setWordWrap(True)
        self.addWidget(value_label, row, 1, 1, 1)

    def finalize(self):
        self.addWidget(HorizontalLine(), self.rowCount(), 0, 1, 2)

    def set_details(self, details: List[Tuple]):
        for title, value in details:
            self.push_row(title, value)
        self.finalize()
