import json
import os
import platform
from functools import partial
from typing import (
    List,
    Optional,
    Dict,
    Union
)

from qgis.PyQt import sip
from qgis.PyQt.QtCore import (
    Qt,
    pyqtSignal
)
from qgis.PyQt.QtGui import (
    QPainter,
    QColor,
    QBrush,
    QPen
)
from qgis.PyQt.QtNetwork import QNetworkReply
from qgis.PyQt.QtWidgets import (
    QFrame,
    QVBoxLayout,
    QSizePolicy,
    QWidget,
    QLabel,
    QStylePainter
)
from qgis.gui import QgsScrollArea

from .datasets_browser_widget import DatasetsBrowserWidget
from .enums import ExploreMode
from ..api import (
    KoordinatesClient,
    DataBrowserQuery,
    ExplorePanel
)

pluginPath = os.path.split(os.path.dirname(__file__))[0]


class ExplorePanelWidget(QWidget):
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
        """
        Cancels any active request
        """
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


class ResultsPanel(QWidget):
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
        if self.current_mode == ExploreMode.Browse:
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
