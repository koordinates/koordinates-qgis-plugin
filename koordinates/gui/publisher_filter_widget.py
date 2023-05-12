import json
import platform
from functools import partial
from typing import (
    Optional,
    List
)

from qgis.PyQt import sip
from qgis.PyQt.QtCore import (
    Qt,
    QAbstractItemModel,
    QObject,
    QModelIndex,
    QSize,
    QRectF,
    QPointF,
    QSortFilterProxyModel
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
    QRadioButton,
    QButtonGroup,
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
from .thumbnails import GenericThumbnailManager
from ..api import (
    KoordinatesClient,
    DataBrowserQuery,
    AccessType,
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
    THUMBNAIL_MARGIN = 5

    def __init__(self, parent: Optional[QObject] = None):
        super().__init__(parent)

    def sizeHint(self, option, index):
        return QSize(0, int(QFontMetrics(option.font).height() * 4.5))

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
                background_color = '#f5f5f7'

            thumbnail_image = index.data(PublisherModel.ThumbnailRole)
            painter.setPen(Qt.NoPen)
            painter.setBrush(QBrush(QColor(background_color)))
            painter.drawPath(path)

            if thumbnail_image and not thumbnail_image.isNull():
                if publisher.publisher_type == PublisherType.Publisher:
                    scaled = thumbnail_image.scaled(
                        QSize(
                            int(thumbnail_rect.width()) - 2 * self.THUMBNAIL_MARGIN,
                            int(thumbnail_image.height()) - 2 * self.THUMBNAIL_MARGIN),
                        Qt.KeepAspectRatio,
                        Qt.SmoothTransformation)
                else:
                    scaled = DatasetGuiUtils.crop_image_to_circle(
                        thumbnail_image, thumbnail_image.height()
                    )

                center_x = int((thumbnail_rect.width() - scaled.width()) / 2)
                center_y = int((thumbnail_rect.height() - scaled.height()) / 2)
                painter.drawImage(QRectF(thumbnail_rect.left() + center_x,
                                         thumbnail_rect.top() + center_y,
                                         scaled.width(), scaled.height()),
                                  scaled)

        heading_font_size = 10
        if platform.system() == 'Darwin':
            heading_font_size = 12

        font = QFont(option.font)
        metrics = QFontMetrics(font)
        font.setPointSizeF(heading_font_size)
        font.setBold(True)
        painter.setFont(font)

        left_text_edge = inner_rect.left() + self.THUMBNAIL_WIDTH + \
                         self.HORIZONTAL_MARGIN * 2

        if publisher.publisher_type == PublisherType.Publisher:
            line_heights = [1.2, 2.1, 3.0]
        else:
            line_heights = [1.6, 0, 2.6]

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

    def _load_next_results(self):
        self._current_reply = KoordinatesClient.instance().publishers_async(
            publisher_type=self.publisher_type,
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
            # hmm, how to know the publisher type when returning All results?
            if 'user:' in p['id']:
                publisher = Publisher(PublisherType.User, p)
            else:
                publisher = Publisher(PublisherType.Publisher, p)
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


class PublisherFilterModel(QSortFilterProxyModel):
    """
    Sort/filter model for publishers
    """

    def __init__(self, parent: Optional[QObject] = None):
        super().__init__(parent)
        self.setDynamicSortFilter(True)

        self._filter_string: str = ''

    def set_filter_string(self, filter_str: str):
        self._filter_string = filter_str
        self.invalidateFilter()

    def filterAcceptsRow(self, row: int, parent: QModelIndex) -> bool:
        if not self._filter_string:
            return True

        parent_index = self.sourceModel().index(row, 0, parent)
        if self._filter_string.upper() in parent_index.data(
                PublisherModel.TitleRole).upper():
            return True

        return False


class PublisherListView(QListView):
    """
    Custom list view for publishers
    """

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)

        self.publisher_model = PublisherModel(self)
        self.filter_model = PublisherFilterModel(self)
        self.filter_model.setSourceModel(self.publisher_model)

        self.setModel(self.filter_model)
        delegate = PublisherDelegate(self)
        self.setItemDelegate(delegate)

        self.setFrameShape(QFrame.NoFrame)
        self.viewport().setStyleSheet(
            "#qt_scrollarea_viewport{ background: transparent; }")

        self.setVerticalScrollMode(QAbstractItemView.ScrollPerPixel)


class PublisherSelectionWidget(QWidget):
    """
    Custom widget for selecting publishers
    """

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)

        vl = QVBoxLayout()
        self.filter_edit = QgsFilterLineEdit()
        self.filter_edit.setShowClearButton(True)
        self.filter_edit.setPlaceholderText(self.tr('Search publishers'))
        vl.addWidget(self.filter_edit)

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
            QFontMetrics(self.font()).horizontalAdvance('x') * 60
        )

        self.filter_edit.textChanged.connect(self._filter_changed)

    def _filter_changed(self, text: str):
        self.publisher_list.filter_model.set_filter_string(text)
        self.tab_bar.setCurrentIndex(0)

    def _tab_changed(self, index: int):
        if index > 0:
            self.filter_edit.clear()

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

        self.view = PublisherSelectionWidget()
        self.view.show()

        self.drop_down_widget = QWidget()
        vl = QVBoxLayout()

        self.public_radio = QRadioButton('Public')
        vl.addWidget(self.public_radio)

        self.private_radio = QRadioButton('Me')
        vl.addWidget(self.private_radio)

        self.access_group = QButtonGroup()
        self.access_group.addButton(self.public_radio)
        self.access_group.addButton(self.private_radio)
        self.access_group.setExclusive(False)
        self.access_group.buttonClicked.connect(
            self._access_group_member_clicked)

        self.drop_down_widget.setLayout(vl)

        self.set_contents_widget(self.drop_down_widget)

        self.clear()

    def _access_group_member_clicked(self, clicked_button):
        self._block_changes += 1
        for radio in (self.public_radio,
                      self.private_radio):
            if radio.isChecked() and radio != clicked_button:
                radio.setChecked(False)

        self._block_changes -= 1
        self._update_value()

    def _update_visible_frames(self):
        self.drop_down_widget.adjustSize()
        self._floating_widget.reflow()

    def clear(self):
        self.public_radio.setChecked(False)
        self.private_radio.setChecked(False)
        self._update_visible_frames()
        self._update_value()

    def should_show_clear(self):
        if not self.public_radio.isChecked() and not self.private_radio.isChecked():
            return False

        return super().should_show_clear()

    def _update_value(self):
        text = 'Publishers'

        if self.public_radio.isChecked():
            text = 'Only public data'
        elif self.private_radio.isChecked():
            text = 'Shared with me'

        self.set_current_text(text)
        if not self._block_changes:
            self.changed.emit()

    def apply_constraints_to_query(self, query: DataBrowserQuery):
        if self.public_radio.isChecked():
            query.access_type = AccessType.Public
        elif self.private_radio.isChecked():
            query.access_type = AccessType.Private
        else:
            query.access_type = None

    def set_from_query(self, query: DataBrowserQuery):
        self._block_changes += 1

        self.public_radio.setChecked(query.access_type == AccessType.Public)
        self.private_radio.setChecked(query.access_type == AccessType.Private)

        self._update_value()
        self._update_visible_frames()
        self._block_changes -= 1
