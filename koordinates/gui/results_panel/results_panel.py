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
    DataBrowserQuery
)
from .datasets_browser_widget import DatasetsBrowserWidget
from ..enums import StandardExploreModes
from .explore_panel import ExplorePanelWidget
from .publishers_panel import PublishersPanelWidget
from ...api import Publisher
from .filter_banner import PublisherFilterBannerWidget

pluginPath = os.path.split(os.path.dirname(__file__))[0]


class ResultsPanel(QWidget):
    """
    A panel for showing explore/browse results
    """
    total_count_changed = pyqtSignal(int)
    visible_count_changed = pyqtSignal(int)
    publisher_selected = pyqtSignal(Publisher)
    publisher_cleared = pyqtSignal()

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

        self.publisher_container = QVBoxLayout()
        self.publisher_container.setContentsMargins(0, 12, 0, 12)
        self.publisher_widget = QWidget()
        self.publisher_widget.setLayout(self.publisher_container)
        self.publisher_widget.setSizePolicy(QSizePolicy.Preferred,
                                            QSizePolicy.Maximum)
        self.publisher_widget.hide()
        layout.addWidget(self.publisher_widget)

        self._publisher_banner: Optional[PublisherFilterBannerWidget] = None

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
        self.current_mode: Optional[str] = None

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
        self.cancel_active_requests()
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        self.container_layout.setContentsMargins(0, 6, 6, 6)
        if self.current_mode == StandardExploreModes.Browse and \
                self.child_items and \
                isinstance(self.child_items[0], DatasetsBrowserWidget):
            self.child_items[0].populate(query, context)
            # scroll to top on new search
            self.scroll_area.verticalScrollBar().setValue(0)
        else:
            self.clear_existing_items()

            self.current_mode = StandardExploreModes.Browse

            item = DatasetsBrowserWidget()
            item.set_margins(0, 0, 16, 16)
            item.total_count_changed.connect(self.total_count_changed)
            item.visible_count_changed.connect(self.visible_count_changed)
            item.populate(query, context)
            self.child_items.append(item)
            self.container_layout.addWidget(item)

    def explore(self, section_slug: str, context):
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        self.container_layout.setContentsMargins(0, 6, 6, 6)
        if section_slug not in (
                StandardExploreModes.Browse,
                StandardExploreModes.Publishers):
            self.current_mode = section_slug

        if self._publisher_banner:
            self._publisher_banner.deleteLater()
            self._publisher_banner = None
            self.publisher_widget.hide()
            self.updateGeometry()

        self.clear_existing_items()

        self._start_explore(section_slug, context)

    def set_publisher(self, publisher: Optional[Publisher]):
        """
        Sets the publisher associated with the results
        """
        if publisher:
            if self._publisher_banner and \
                    self._publisher_banner.publisher.id() == publisher.id():
                pass
            else:
                if self._publisher_banner:
                    self._publisher_banner.deleteLater()

                self._publisher_banner = PublisherFilterBannerWidget(
                    publisher)
                self.publisher_container.addWidget(
                    self._publisher_banner)
                self.publisher_widget.show()
                self._publisher_banner.closed.connect(
                    self._remove_publisher_filter)
                self.updateGeometry()
        elif self._publisher_banner:
            self._publisher_banner.deleteLater()
            self._publisher_banner = None

            self.publisher_widget.hide()
            self.updateGeometry()

    def _remove_publisher_filter(self):
        if self._publisher_banner:
            self._publisher_banner.deleteLater()
            self._publisher_banner = None

            self.publisher_widget.hide()
            self.updateGeometry()

        self.publisher_cleared.emit()

    def show_publishers(self, context):
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.container_layout.setContentsMargins(0, 0, 0, 0)
        self.cancel_active_requests()
        self.clear_existing_items()

        item = PublishersPanelWidget()
        item.publisher_selected.connect(self._publisher_selected)
        self.child_items.append(item)
        self.container_layout.addWidget(item)

        if self._publisher_banner:
            self._publisher_banner.deleteLater()
            self._publisher_banner = None
            self.publisher_widget.hide()
            self.updateGeometry()

    def _publisher_selected(self, publisher: Publisher):
        self.publisher_selected.emit(publisher)
        self.set_publisher(publisher)

    def _start_explore(self,
                       section_slug: str,
                       context: Optional[str] = None):
        if self._current_reply is not None and \
                not sip.isdeleted(self._current_reply):
            if self._current_reply.property('slug') == section_slug:
                return

            self._current_reply.abort()
            self._current_reply = None

        if context is not None:
            self._current_context = context

        self._current_reply = KoordinatesClient.instance().explore_async(
            section_slug=section_slug,
            context=self._current_context
        )
        self._current_reply.setProperty('slug', section_slug)
        self._current_reply.finished.connect(
            partial(self._reply_finished, self._current_reply, section_slug))
        self.setCursor(Qt.WaitCursor)

    def _reply_finished(self,
                        reply: QNetworkReply,
                        section_slug: str):
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

        # we shouldn't need this logic, but the API currently returns
        # some items which are not present in the filter param!
        for panel in result['panels']:
            # filter panel items to supported ones
            panel['items'] = [item for item in panel['items']
                              if item['kind'].startswith('layer.')]
            # and then completely skip any empty panels
            if panel['items']:
                filtered_panels.append(panel)

        for panel in filtered_panels:
            item = ExplorePanelWidget(panel, mode=section_slug)
            self.child_items.append(item)
            self.container_layout.addWidget(item)

        self.setCursor(Qt.ArrowCursor)
