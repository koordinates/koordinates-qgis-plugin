import json
import math
import os
from functools import partial
from typing import (
    List,
    Optional
)

from qgis.PyQt import sip
from qgis.PyQt.QtCore import (
    Qt,
    pyqtSignal
)
from qgis.PyQt.QtGui import (
    QFontMetrics
)
from qgis.PyQt.QtNetwork import QNetworkReply
from qgis.PyQt.QtWidgets import (
    QHBoxLayout,
    QFrame,
    QLabel,
    QToolButton,
    QVBoxLayout,
    QSizePolicy,
    QWidget
)
from qgis.gui import QgsScrollArea

from .datasets_browser_widget import DatasetsBrowserWidget
from ..api import (
    KoordinatesClient,
    PAGE_SIZE,
    DataBrowserQuery,
    ExplorePanel
)
from .enums import ExploreMode


pluginPath = os.path.split(os.path.dirname(__file__))[0]


class ResultsPanel(QWidget):
    datasetDetailsRequested = pyqtSignal(dict)
    total_count_changed = pyqtSignal(int)
    visible_count_changed = pyqtSignal(int)

    def __init__(self):
        super().__init__()

        self.scroll_area = QgsScrollArea()
        self.scroll_area.setSizePolicy(QSizePolicy.Preferred,
                                       QSizePolicy.Preferred)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        self.scroll_area.setWidgetResizable(True)
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)

        self.container = QWidget()
        self.container_layout = QVBoxLayout()
        self.container.setLayout(self.container_layout)

        self.scroll_area.setWidget(self.container)

        layout.addWidget(self.scroll_area)
        self.setLayout(layout)

        self.scroll_area.setFrameShape(QFrame.NoFrame)
        self.scroll_area.setStyleSheet("#qt_scrollarea_viewport{ background: transparent; }")

        self.child_items: List[DatasetsBrowserWidget] = []

        self.setMinimumWidth(370)
        self.current_mode: Optional[ExploreMode] = None

    def cancel_active_requests(self):
        """
        Cancels any active request
        """
        for item in self.child_items:
            item.cancel_active_requests()

    def clear_existing_items(self):
        for item in self.child_items:
            self.container_layout.removeWidget(item)
            item.deleteLater()
        self.child_items.clear()

    def populate(self, query: DataBrowserQuery, context):
        if self.current_mode == ExploreMode.Browse:
            self.child_items[0].populate(query, context)
            # scroll to top on new search
            self.scroll_area.verticalScrollBar().setValue(0)
        else:
            self.clear_existing_items()

            self.current_mode = ExploreMode.Browse

            item = DatasetsBrowserWidget()
            item.populate(query, context)
            self.child_items.append(item)
            self.container_layout.addWidget(item)

    def explore(self, panel: ExplorePanel, context):
        if panel == ExploreMode.Recent:
            self.current_mode = ExploreMode.Recent
        elif panel == ExploreMode.Popular:
            self.current_mode = ExploreMode.Popular

        self.clear_existing_items()

        item = DatasetsBrowserWidget()
        item.explore(panel, context)
        self.child_items.append(item)
        self.container_layout.addWidget(item)
