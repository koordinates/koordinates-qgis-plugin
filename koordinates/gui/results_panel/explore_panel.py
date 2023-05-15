import os
import platform
from typing import (
    Optional,
    Dict
)

from qgis.PyQt.QtGui import (
    QPainter,
    QColor,
    QBrush,
    QPen
)
from qgis.PyQt.QtWidgets import (
    QVBoxLayout,
    QWidget,
    QLabel,
    QStylePainter
)

from .results_panel_widget import ResultsPanelWidget
from koordinates.gui.results_panel.datasets_browser_widget import DatasetsBrowserWidget

pluginPath = os.path.split(os.path.dirname(__file__))[0]


class ExplorePanelWidget(ResultsPanelWidget):
    """
    Results panel widget for "explore" style panels
    """

    CORNER_RADIUS = 4

    def __init__(self, content: Dict, parent: Optional[QWidget] = None):
        super().__init__(parent)

        title_label = QLabel()
        title_label.setWordWrap(True)

        main_title_size = 14
        font_scale = self.screen().logicalDotsPerInch() / 92

        if platform.system() == 'Darwin':
            # fonts looks smaller on a mac, where things "just work" :P
            main_title_size = 17
        elif font_scale > 1:
            main_title_size = int(15 / font_scale)

        title_label.setText(
            f"""<p style="line-height: 130%;
                font-size: {main_title_size}pt;
                font-family: Arial, Sans"><b>{content['title']}</b>"""
        )

        self.browser = DatasetsBrowserWidget()
        self.browser.set_datasets(item['content'] for item in content['items'])

        vl = QVBoxLayout()
        vl.setContentsMargins(12, 12, 12, 0)
        vl.addWidget(title_label)
        vl.addWidget(self.browser)

        self.setLayout(vl)

    def cancel_active_requests(self):
        self.browser.cancel_active_requests()

    def paintEvent(self, event):
        painter = QStylePainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)

        painter.save()
        brush = QBrush(QColor(255, 255, 255))
        painter.setBrush(brush)
        pen = QPen(QColor('#dddddd'))

        painter.setPen(pen)
        painter.drawRoundedRect(self.rect(),
                                self.CORNER_RADIUS,
                                self.CORNER_RADIUS)
        painter.restore()
