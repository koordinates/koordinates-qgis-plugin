import json
import platform
from functools import partial
from typing import (
    Optional,
    List,
    Dict
)

from qgis.PyQt import sip
from qgis.PyQt.QtCore import (
    pyqtSignal,
    Qt,
    QAbstractItemModel,
    QObject,
    QModelIndex,
    QSize,
    QRectF,
    QPointF
)
from qgis.PyQt.QtGui import (
    QFontMetrics,
    QPainter,
    QBrush,
    QPen,
    QColor,
    QFont,
    QPainterPath
)
from qgis.PyQt.QtNetwork import (
    QNetworkReply
)
from qgis.PyQt.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QStyledItemDelegate,
    QStyleOptionViewItem,
    QAbstractItemView,
    QListView,
    QFrame
)
from qgis.gui import (
    QgsFilterLineEdit
)

from .dataset_utils import DatasetGuiUtils
from .explore_tab_bar import FlatUnderlineTabBar
from .filter_widget_combo_base import FilterWidgetComboBase
from .gui_utils import GuiUtils
from .rounded_highlight_box import RoundedHighlightBox
from .thumbnails import GenericThumbnailManager
from .user_avatar_generator import UserAvatarGenerator
from ..api import (
    KoordinatesClient,
    DataBrowserQuery,
    Publisher,
)
from ..api import PublisherType


class PublisherDelegate(QStyledItemDelegate):
    """
    Custom delegate for rendering publisher details in a list
    """

    THUMBNAIL_CORNER_RADIUS = 7
    VERTICAL_MARGIN = 7
    HORIZONTAL_MARGIN = 5
    THUMBNAIL_WIDTH = 118
    THUMBNAIL_MARGIN = 8

    def __init__(self, parent: Optional[QObject] = None):
        super().__init__(parent)

    def sizeHint(self, option, index):
        line_scale = 1
        if platform.system() == 'Darwin':
            line_scale = 1.3

        return QSize(0, int(QFontMetrics(option.font).height()
                            * 4.5
                            * line_scale))

    def paint(self, painter: QPainter, option: QStyleOptionViewItem,
              index: QModelIndex):
        publisher: Publisher = index.data(PublisherModel.PublisherRole)

        painter.save()
        painter.setRenderHint(QPainter.Antialiasing, True)
        painter.setRenderHint(QPainter.TextAntialiasing, True)
        painter.setRenderHint(QPainter.SmoothPixmapTransform, True)

        pen = QPen(QColor('#dddddd'))
        pen.setWidth(0)
        pen.setCosmetic(True)
        painter.setPen(pen)
        painter.setBrush(QBrush(QColor(255, 255, 255)))

        rect = QRectF(option.rect)
        inner_rect = rect
        inner_rect.adjust(self.HORIZONTAL_MARGIN,
                          self.VERTICAL_MARGIN,
                          -self.HORIZONTAL_MARGIN,
                          -self.VERTICAL_MARGIN)
        painter.drawRoundedRect(inner_rect,
                                self.THUMBNAIL_CORNER_RADIUS,
                                self.THUMBNAIL_CORNER_RADIUS)

        if not publisher:
            return

        thumbnail_rect = inner_rect
        thumbnail_rect.setWidth(self.THUMBNAIL_WIDTH)

        path = QPainterPath()

        path.moveTo(thumbnail_rect.left() + self.THUMBNAIL_CORNER_RADIUS,
                    thumbnail_rect.top())
        path.lineTo(thumbnail_rect.right(), thumbnail_rect.top())
        path.lineTo(thumbnail_rect.right(), thumbnail_rect.bottom())
        path.lineTo(thumbnail_rect.left() + self.THUMBNAIL_CORNER_RADIUS,
                    thumbnail_rect.bottom())
        path.arcTo(thumbnail_rect.left(),
                   thumbnail_rect.bottom() - self.THUMBNAIL_CORNER_RADIUS * 2,
                   self.THUMBNAIL_CORNER_RADIUS * 2,
                   self.THUMBNAIL_CORNER_RADIUS * 2,
                   270, -90
                   )
        path.lineTo(thumbnail_rect.left(),
                    thumbnail_rect.top() + self.THUMBNAIL_CORNER_RADIUS)
        path.arcTo(thumbnail_rect.left(),
                   thumbnail_rect.top(),
                   self.THUMBNAIL_CORNER_RADIUS * 2,
                   self.THUMBNAIL_CORNER_RADIUS * 2,
                   180, -90
                   )

        if publisher.theme:
            background_color = publisher.theme.background_color()
            if not background_color:
                if publisher.publisher_type == PublisherType.User:
                    background_color = QColor('#f5f5f7')
                else:
                    background_color = QColor('#555657')

            thumbnail_image = index.data(PublisherModel.ThumbnailRole)
            painter.setPen(Qt.NoPen)
            painter.setBrush(QBrush(background_color))
            painter.drawPath(path)

            if thumbnail_image and not thumbnail_image.isNull():
                if publisher.publisher_type == PublisherType.Publisher:
                    max_thumbnail_width = int(thumbnail_rect.width()) \
                                          - 2 * self.THUMBNAIL_MARGIN
                    max_thumbnail_height = \
                        int(min(thumbnail_rect.height(),
                                thumbnail_image.height())) \
                        - 2 * self.THUMBNAIL_MARGIN
                    scaled = thumbnail_image.scaled(
                        QSize(max_thumbnail_width, max_thumbnail_height),
                        Qt.KeepAspectRatio,
                        Qt.SmoothTransformation)
                else:
                    scaled = DatasetGuiUtils.crop_image_to_circle(
                        thumbnail_image, thumbnail_image.height()
                    )
            elif publisher.publisher_type == PublisherType.User:
                scaled = UserAvatarGenerator.get_avatar(publisher.name())
            else:
                scaled = GuiUtils.get_svg_as_image('globe.svg',
                                                   40, 40)

            center_x = int((thumbnail_rect.width() - scaled.width()) / 2)
            center_y = int((thumbnail_rect.height() - scaled.height()) / 2)
            painter.drawImage(QRectF(thumbnail_rect.left() + center_x,
                                     thumbnail_rect.top() + center_y,
                                     scaled.width(), scaled.height()),
                              scaled)

        heading_font_size = 10
        line_scale = 1
        if platform.system() == 'Darwin':
            heading_font_size = 12
            line_scale = 1.3

        font = QFont(option.font)
        metrics = QFontMetrics(font)
        font.setPointSizeF(heading_font_size)
        font.setBold(True)
        painter.setFont(font)

        left_text_edge = inner_rect.left() + self.THUMBNAIL_WIDTH + \
            self.HORIZONTAL_MARGIN * 2

        if publisher.publisher_type == PublisherType.Publisher:
            line_heights = [1.2 * line_scale,
                            2.1 * line_scale,
                            3.0 * line_scale]
        else:
            line_heights = [1.6 * line_scale,
                            0,
                            2.6 * line_scale]

        painter.setBrush(Qt.NoBrush)
        painter.setPen(QPen(QColor(0, 0, 0)))
        painter.drawText(QPointF(left_text_edge,
                                 inner_rect.top() + int(
                                     metrics.height() * line_heights[0])),
                         publisher.name())

        font.setBold(False)
        painter.setFont(font)

        if line_heights[1]:
            painter.drawText(QPointF(left_text_edge,
                                     inner_rect.top() + int(
                                         metrics.height() * line_heights[1])),
                             'via ' + publisher.site.name())

        painter.setPen(QPen(QColor(0, 0, 0, 100)))
        painter.drawText(QPointF(left_text_edge,
                                 inner_rect.top() + int(
                                     metrics.height() * line_heights[2])),
                         '{} datasets '.format(DatasetGuiUtils.format_number(
                             publisher.dataset_count())))

        painter.restore()


class PublisherModel(QAbstractItemModel):
    """
    Qt model for publishers
    """

    TitleRole = Qt.UserRole + 1
    PublisherRole = Qt.UserRole + 2
    ThumbnailRole = Qt.UserRole + 3

    def __init__(self, parent: Optional[QObject] = None):
        super().__init__(parent)

        self._current_reply = None
        self.available_count = 0
        self.publisher_type = PublisherType.Publisher
        self._filter_string: Optional[str] = None
        self.publishers: List[Publisher] = []
        self.current_page = 1
        self._load_next_results()

        self._thumbnail_manager = GenericThumbnailManager()
        self._thumbnail_manager.downloaded.connect(self._thumbnail_downloaded)

    def set_publisher_type(self, publisher_type: PublisherType):
        if self.publisher_type == publisher_type:
            return

        self.beginResetModel()
        self.publisher_type = publisher_type
        self.publishers = []
        self._current_reply = None
        self.available_count = 0
        self.current_page = 1
        self.endResetModel()

        self._load_next_results()

    def set_filter_string(self, filter_string: str):
        """
        Sets a text filter for the view
        """
        if filter_string == self._filter_string:
            return

        self.beginResetModel()
        self._filter_string = filter_string
        self.publishers = []
        self._current_reply = None
        self.available_count = 0
        self.current_page = 1
        self.endResetModel()

        self._load_next_results()

    def _load_next_results(self):
        self._current_reply = KoordinatesClient.instance().publishers_async(
            publisher_type=self.publisher_type,
            filter_string=self._filter_string,
            page=self.current_page
        )
        self._current_reply.finished.connect(
            partial(self._reply_finished, self._current_reply))

    def _reply_finished(self, reply: QNetworkReply):
        if sip.isdeleted(self):
            return

        if reply != self._current_reply:
            # an old reply we don't care about anymore
            return

        self._current_reply = None

        if reply.error() == QNetworkReply.OperationCanceledError:
            return

        if reply.error() == QNetworkReply.ContentNotFoundError:
            self.available_count = 0
            return

        if reply.error() != QNetworkReply.NoError:
            print('error occurred :(')
            return
        # self.error_occurred.emit(request.reply().errorString())

        tokens = reply.rawHeader(b"X-Resource-Range").data().decode().split(
            "/")
        if not self.publishers:
            self.available_count = int(tokens[-1])

        self.current_page += 1

        result = json.loads(reply.readAll().data().decode())
        self.beginInsertRows(QModelIndex(), len(self.publishers),
                             len(self.publishers) + len(result) - 1)

        thumbnail_urls = set()
        for p in result:
            publisher = Publisher(p)
            self.publishers.append(publisher)
            if publisher.theme.logo():
                thumbnail_urls.add(publisher.theme.logo())

        self.endInsertRows()

        for thumbnail_url in thumbnail_urls:
            self._thumbnail_manager.download_thumbnail(thumbnail_url)

    # Qt model interface

    # pylint: disable=missing-docstring, unused-arguments
    def index(self, row, column, parent=QModelIndex()):
        if column < 0 or column >= self.columnCount():
            return QModelIndex()

        if not parent.isValid() and 0 <= row < len(self.publishers):
            return self.createIndex(row, column)

        return QModelIndex()

    def parent(self, index):
        return QModelIndex()  # all are top level items

    def rowCount(self, parent=QModelIndex()):
        if not parent.isValid():
            return len(self.publishers)
        # no child items
        return 0

    def columnCount(self, parent=QModelIndex()):
        return 1

    def data(self, index, role=Qt.DisplayRole):
        publisher = self.index2publisher(index)
        if publisher:
            if role == self.PublisherRole:
                return publisher

            if role == self.ThumbnailRole:
                return self._thumbnail_manager.thumbnail(
                    publisher.theme.logo())

            if role == self.TitleRole:
                return publisher.name()

        return None

    def flags(self, index):
        f = super().flags(index)
        if not index.isValid():
            return f

        return f | Qt.ItemIsEnabled

    def canFetchMore(self, QModelIndex):
        if not self.publishers:
            return True
        return len(self.publishers) < self.available_count

    def fetchMore(self, QModelIndex):
        if self._current_reply:
            return

        self._load_next_results()

    # pylint: enable=missing-docstring, unused-arguments
    def index2publisher(self, index: QModelIndex) -> Optional[Publisher]:
        """
        Returns the publisher at the given model index
        """
        if not index.isValid() or index.row() < 0 or index.row() >= len(
                self.publishers):
            return None

        return self.publishers[index.row()]

    def _thumbnail_downloaded(self, url: str):
        """
        Called when a thumbnail is downloaded
        """
        for row, publisher in enumerate(self.publishers):
            if publisher.theme.logo() == url:
                index = self.index(row, 0)
                self.dataChanged.emit(index, index)


class PublisherListView(QListView):
    """
    Custom list view for publishers
    """

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)

        self.publisher_model = PublisherModel(self)
        self.setModel(self.publisher_model)
        delegate = PublisherDelegate(self)
        self.setItemDelegate(delegate)

        self.setFrameShape(QFrame.NoFrame)
        self.viewport().setStyleSheet(
            "#qt_scrollarea_viewport{ background: transparent; }")

        self.setVerticalScrollMode(QAbstractItemView.ScrollPerPixel)

    def set_filter_string(self, filter_string: str):
        """
        Sets a text filter for the view
        """
        self.publisher_model.set_filter_string(filter_string)


class PublisherSelectionWidget(QWidget):
    """
    Custom widget for selecting publishers
    """

    FACETS_REPLY = {}

    selection_changed = pyqtSignal(Publisher)

    def __init__(self,
                 highlight_search_box: bool = False,
                 parent: Optional[QWidget] = None):
        super().__init__(parent)

        self._current_facets_reply: Optional[QNetworkReply] = None

        vl = QVBoxLayout()
        self.filter_edit = QgsFilterLineEdit()
        self.filter_edit.setShowClearButton(True)
        self.filter_edit.setPlaceholderText(self.tr('Search publishers'))
        if not highlight_search_box:
            vl.addWidget(self.filter_edit)
        else:
            search_highlight = RoundedHighlightBox()
            sub_layout = QVBoxLayout()
            sub_layout.addWidget(self.filter_edit)
            search_highlight.setLayout(sub_layout)
            vl.addWidget(search_highlight)

        self.setCursor(Qt.PointingHandCursor)

        self.tab_bar = FlatUnderlineTabBar()
        self.tab_bar.addTab(self.tr('All'))
        self.tab_bar.addTab(self.tr('Publishers'))
        self.tab_bar.addTab(self.tr('Users'))
        self.tab_bar.addTab(self.tr('Mirrored'))
        self.tab_bar.setCurrentIndex(1)

        self.tab_bar.currentChanged.connect(self._tab_changed)
        vl.addWidget(self.tab_bar)

        self.publisher_list = PublisherListView()
        vl.addWidget(self.publisher_list, 1)
        self.setStyleSheet(
            "PublisherSelectionWidget{ background: white; }")
        self.setLayout(vl)

        self.setMinimumWidth(
            QFontMetrics(self.font()).horizontalAdvance('x') * 68
        )
        self.setMinimumHeight(
            QFontMetrics(self.font()).height() * 20
        )

        self.publisher_list.selectionModel().selectionChanged.connect(
            self._selection_changed
        )

        self.filter_edit.textChanged.connect(self._filter_changed)

        self._load_total_counts()

    def _load_total_counts(self):
        """
        Loads the total counts for the publisher types
        """
        if PublisherSelectionWidget.FACETS_REPLY and \
                not self.filter_edit.text():
            self._load_facet_reply(PublisherSelectionWidget.FACETS_REPLY)
            return

        self._current_facets_reply = \
            KoordinatesClient.instance().publishers_async(
                publisher_type=None,
                filter_string=self.filter_edit.text(),
                is_facets=True
            )
        self._current_facets_reply.finished.connect(
            partial(self._facets_reply_finished, self._current_facets_reply))

    def _facets_reply_finished(self, reply: QNetworkReply):
        if sip.isdeleted(self):
            return

        if reply != self._current_facets_reply:
            # an old reply we don't care about anymore
            return

        self._current_facets_reply = None

        if reply.error() == QNetworkReply.OperationCanceledError:
            return

        if reply.error() != QNetworkReply.NoError:
            print('error occurred :(')
            return
        # self.error_occurred.emit(request.reply().errorString())

        reply_content = json.loads(
            reply.readAll().data().decode())
        if not self.filter_edit.text():
            PublisherSelectionWidget.FACETS_REPLY = reply_content
            self._load_facet_reply(PublisherSelectionWidget.FACETS_REPLY)

        else:
            self._load_facet_reply(reply_content)

    def _load_facet_reply(self, reply: Dict):
        """
        Updates tab text based on the facet's reply
        """
        overall_total = 0
        for publisher_type in reply.get(
                'type', []
        ):
            publisher_key = publisher_type.get('key', [])
            total_count = publisher_type.get('total', 0)
            overall_total += total_count

            if publisher_key == 'site':
                self.tab_bar.setTabText(
                    1,
                    self.tr('Publishers ({})'.format(total_count))
                )
            elif publisher_key == 'mirror':
                self.tab_bar.setTabText(
                    3,
                    self.tr('Mirrored ({})'.format(total_count))
                )
            elif publisher_key == 'user':
                self.tab_bar.setTabText(
                    2,
                    self.tr('Users ({})'.format(total_count))
                )

        self.tab_bar.setTabText(
            0,
            self.tr('All ({})'.format(overall_total))
        )

    def _filter_changed(self, text: str):
        self.publisher_list.set_filter_string(text)
        self.tab_bar.setCurrentIndex(0)
        self._load_total_counts()

    def _selection_changed(self, selected, _):
        try:
            selection: Optional[Publisher] = selected[0].topLeft().data(
                PublisherModel.PublisherRole
            )
            self.selection_changed.emit(selection)
        except IndexError:
            return

    def _tab_changed(self, index: int):
        if index == 0:
            self.publisher_list.publisher_model.set_publisher_type(
                PublisherType.All)
        elif index == 1:
            self.publisher_list.publisher_model.set_publisher_type(
                PublisherType.Publisher)
        elif index == 2:
            self.publisher_list.publisher_model.set_publisher_type(
                PublisherType.User)
        elif index == 3:
            self.publisher_list.publisher_model.set_publisher_type(
                PublisherType.Mirror)


class PublisherFilterWidget(FilterWidgetComboBase):
    """
    Custom widget for publisher based filtering
    """

    def __init__(self, parent):
        super().__init__(parent)

        self.drop_down_widget = PublisherSelectionWidget()
        self.drop_down_widget.selection_changed.connect(
            self._selection_changed
        )

        self.set_contents_widget(self.drop_down_widget)

        self._current_publisher: Optional[Publisher] = None

        self.clear()

    def current_publisher(self) -> Optional[Publisher]:
        """
        Returns the selected publisher, if one
        """
        return self._current_publisher

    def _selection_changed(self, publisher: Publisher):
        self._current_publisher = publisher
        self._update_value()
        self.collapse()

    def _update_visible_frames(self):
        self.drop_down_widget.adjustSize()
        self._floating_widget.reflow()

    def clear(self):
        self._current_publisher = None
        self._update_value()

    def should_show_clear(self):
        if self._current_publisher is None:
            return False

        return super().should_show_clear()

    def _update_value(self):
        text = 'Publishers'

        if self._current_publisher:
            text = self._current_publisher.name()

        self.set_current_text(text)
        if not self._block_changes:
            self.changed.emit()

    def apply_constraints_to_query(self, query: DataBrowserQuery):
        if self._current_publisher:
            query.publisher = self._current_publisher

    def set_from_query(self, query: DataBrowserQuery):
        self._block_changes += 1

        if query.publisher:
            self._current_publisher = query.publisher

        self._update_value()
        self._update_visible_frames()
        self._block_changes -= 1
