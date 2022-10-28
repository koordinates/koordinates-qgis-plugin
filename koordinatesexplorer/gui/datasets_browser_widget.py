import json
import math
import os
from functools import partial
from typing import Optional

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

from .response_table_layout import ResponsiveTableWidget
from ..api import (
    KoordinatesClient,
    PAGE_SIZE,
    DataBrowserQuery
)

pluginPath = os.path.split(os.path.dirname(__file__))[0]


class DatasetsBrowserWidget(QWidget):
    datasetDetailsRequested = pyqtSignal(dict)
    total_count_changed = pyqtSignal(int)
    visible_count_changed = pyqtSignal(int)

    def __init__(self):
        super().__init__()

        scroll_area = QgsScrollArea()
        scroll_area.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll_area.setWidgetResizable(True)
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)

        self.table_widget = ResponsiveTableWidget()
        scroll_area.setWidget(self.table_widget)

        layout.addWidget(scroll_area)
        self.setLayout(layout)

        self.setObjectName('DatasetsBrowserWidget')
        scroll_area.setFrameShape(QFrame.NoFrame)
        scroll_area.setStyleSheet("#qt_scrollarea_viewport{ background: transparent; }")

        self._current_query: Optional[DataBrowserQuery] = None
        self._current_reply: Optional[QNetworkReply] = None
        self._current_context = None
        self._load_more_widget = None
        self._no_records_widget = None
        self._datasets = []
        self.setMinimumWidth(370)

    def cancel_active_requests(self):
        """
        Cancels any active request
        """
        if self._current_reply is not None and \
                not sip.isdeleted(self._current_reply):
            self._current_reply.abort()

        self._current_reply = None

    def _create_temporary_items_for_page(self):
        for i in range(PAGE_SIZE):
            self.table_widget.push_empty_widget()

    def populate(self, query: DataBrowserQuery, context):
        self.table_widget.setUpdatesEnabled(False)
        self.table_widget.clear()

        self._datasets = []
        self._create_temporary_items_for_page()
        self.table_widget.setUpdatesEnabled(True)

        self._load_more_widget = None
        self._no_records_widget = None

        self.visible_count_changed.emit(-1)
        self._fetch_records(query, context)

    def _fetch_records(self,
                       query: Optional[DataBrowserQuery] = None,
                       context: Optional[str] = None,
                       page: int = 1):
        if self._current_reply is not None and not sip.isdeleted(self._current_reply):
            self._current_reply.abort()
            self._current_reply = None

        if query is not None:
            self._current_query = query
        if context is not None:
            self._current_context = context

        self._current_reply = KoordinatesClient.instance().datasets_async(
            query=self._current_query,
            context=self._current_context,
            page=page
        )
        self._current_reply.finished.connect(partial(self._reply_finished, self._current_reply))
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
        #            self.error_occurred.emit(request.reply().errorString())

        datasets = json.loads(reply.readAll().data().decode())
        tokens = reply.rawHeader(b"X-Resource-Range").data().decode().split("/")
        total = tokens[-1]
        self.total_count_changed.emit(int(total))
        last = tokens[0].split("-")[-1]
        finished = last == total

        self.table_widget.setUpdatesEnabled(False)
        self._add_datasets(datasets)
        self._datasets.extend(datasets)
        self.visible_count_changed.emit(len(self._datasets))

        self.setCursor(Qt.ArrowCursor)
        self.table_widget.remove_empty_widgets()

        if not finished and not self._load_more_widget:
            self._load_more_widget = LoadMoreItemWidget()
            self._load_more_widget.load_more.connect(self.load_more)

            self.table_widget.push_widget(self._load_more_widget)

        elif finished and self._load_more_widget:
            self.table_widget.remove_widget(self._load_more_widget)
            self._load_more_widget = None

        if total == '0' and not self._no_records_widget:
            self._no_records_widget = NoRecordsItemWidget()
            self.table_widget.push_widget(self._no_records_widget)
        elif total != '0' and self._no_records_widget:
            self.table_widget.remove_widget(self._no_records_widget)
            self._no_records_widget = None

        self.table_widget.setUpdatesEnabled(True)

    def _add_datasets(self, datasets):
        for i, dataset in enumerate(datasets):
            self.table_widget.push_dataset(dataset)

    def load_more(self):
        next_page = math.ceil(len(self._datasets) / PAGE_SIZE) + 1

        self.table_widget.remove_widget(self._load_more_widget)
        self._load_more_widget = None
        self._create_temporary_items_for_page()
        self._fetch_records(page=next_page)


class LoadMoreItemWidget(QFrame):
    load_more = pyqtSignal()

    def __init__(self):
        QFrame.__init__(self)
        self.btnLoadMore = QToolButton()
        self.btnLoadMore.setText("Load more...")
        self.btnLoadMore.clicked.connect(self.load_more)

        layout = QHBoxLayout()
        layout.addStretch()
        layout.addWidget(self.btnLoadMore)
        layout.addStretch()
        self.setLayout(layout)


class NoRecordsItemWidget(QFrame):
    def __init__(self):
        QFrame.__init__(self)
        self.no_data_frame = QLabel("No data available")

        self.no_data_frame.setStyleSheet(
            """
            QLabel {
                background-color: #ffffff;
                border: 1px solid #cccccc;
                border-radius: 4px;
                padding: 29px 23px 29px 23px;
                color: #a4a6a6;
                }
            """
        )

        top_padding = QFontMetrics(self.font()).height() * 3
        vl = QVBoxLayout()
        vl.addSpacing(top_padding)

        layout = QHBoxLayout()
        layout.addStretch()
        layout.addWidget(self.no_data_frame)
        layout.addStretch()
        vl.addLayout(layout)
        self.setLayout(vl)
