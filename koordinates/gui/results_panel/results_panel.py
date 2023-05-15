import json
import os
from functools import partial
from typing import (
    List,
    Optional,
    Union
)

from qgis.PyQt import sip
from qgis.PyQt.QtCore import (
    Qt,
    pyqtSignal
)
from qgis.PyQt.QtNetwork import QNetworkReply
from qgis.PyQt.QtWidgets import (
    QFrame,
    QVBoxLayout,
    QSizePolicy,
    QWidget
)
from qgis.gui import QgsScrollArea

from koordinates.api import (
    KoordinatesClient,
    DataBrowserQuery,
    ExplorePanel
)
from koordinates.gui.results_panel.datasets_browser_widget import DatasetsBrowserWidget
from ..enums import ExploreMode
from .explore_panel import ExplorePanelWidget

pluginPath = os.path.split(os.path.dirname(__file__))[0]


class ResultsPanel(QWidget):
    """
    A panel for showing explore/browse results
    """
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
        self.scroll_area.setStyleSheet(
            "#qt_scrollarea_viewport{ background: transparent; }")

        self.child_items: List[
            Union[DatasetsBrowserWidget, ExplorePanelWidget]] = []

        self.setMinimumWidth(370)
        self.current_mode: Optional[ExploreMode] = None

        self._current_reply: Optional[QNetworkReply] = None
        self._current_context = None

    def cancel_active_requests(self):
        """
        Cancels any active request
        """
        if self._current_reply is not None and \
                not sip.isdeleted(self._current_reply):
            self._current_reply.abort()

        self._current_reply = None

        for item in self.child_items:
            item.cancel_active_requests()

    def clear_existing_items(self):
        for item in self.child_items:
            self.container_layout.removeWidget(item)
            item.deleteLater()
        self.child_items.clear()

    def populate(self, query: DataBrowserQuery, context):
        if self.current_mode == ExploreMode.Browse and \
                self.child_items and \
                isinstance(self.child_items[0], DatasetsBrowserWidget):
            self.child_items[0].populate(query, context)
            # scroll to top on new search
            self.scroll_area.verticalScrollBar().setValue(0)
        else:
            self.clear_existing_items()

            self.current_mode = ExploreMode.Browse

            item = DatasetsBrowserWidget()
            item.total_count_changed.connect(self.total_count_changed)
            item.visible_count_changed.connect(self.visible_count_changed)
            item.populate(query, context)
            self.child_items.append(item)
            self.container_layout.addWidget(item)

    def explore(self, panel: ExplorePanel, context):
        if panel == ExploreMode.Recent:
            self.current_mode = ExploreMode.Recent
        elif panel == ExploreMode.Popular:
            self.current_mode = ExploreMode.Popular

        self.clear_existing_items()

        self._start_explore(panel, context)

    def _start_explore(self,
                       panel: ExplorePanel,
                       context: Optional[str] = None):
        if self._current_reply is not None and \
                not sip.isdeleted(self._current_reply):
            self._current_reply.abort()
            self._current_reply = None

        if context is not None:
            self._current_context = context

        self._current_reply = KoordinatesClient.instance().explore_async(
            panel=panel,
            context=self._current_context
        )
        self._current_reply.finished.connect(
            partial(self._reply_finished, self._current_reply))
        self.setCursor(Qt.WaitCursor)

    def _reply_finished(self, reply: QNetworkReply):
        if sip.isdeleted(self):
            return

        if reply != self._current_reply:
            # an old reply we don't care about anymore
            return

        self._current_reply = None

        if reply.error() == QNetworkReply.OperationCanceledError:
            return

        if reply.error() != QNetworkReply.NoError:
            print('error occurred :(')
            return
        # self.error_occurred.emit(request.reply().errorString())

        result = json.loads(reply.readAll().data().decode())
        if 'panels' not in result:
            print('error occurred :(')
            return

        filtered_panels = []
        for panel in result['panels']:
            if any([item['kind'] in ('layer.vector', 'layer.raster') for item
                    in panel['items']]):
                filtered_panels.append(panel)

        for panel in filtered_panels:
            item = ExplorePanelWidget(panel)
            self.child_items.append(item)
            self.container_layout.addWidget(item)

        self.setCursor(Qt.ArrowCursor)
