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
    QPointF
)
from qgis.PyQt.QtGui import (
    QFontMetrics,
    QPainter,
    QBrush,
    QPen,
    QColor,
    QFont
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
    QListView
)

from .dataset_utils import DatasetGuiUtils
from .filter_widget_combo_base import FilterWidgetComboBase
from ..api import (
    KoordinatesClient,
    DataBrowserQuery,
    AccessType,
    Publisher
)


class PublisherDelegate(QStyledItemDelegate):
    """
    Custom delegate for rendering publisher details in a list
    """

    THUMBNAIL_CORNER_RADIUS = 7
    VERTICAL_MARGIN = 7
    HORIZONTAL_MARGIN = 5
    THUMBNAIL_WIDTH = 118

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

        thumbnail_rect = inner_rect
        thumbnail_rect.setWidth(self.THUMBNAIL_WIDTH)
        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(QColor(255, 0, 0)))
        painter.drawRect(thumbnail_rect)

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

        painter.setBrush(Qt.NoBrush)
        painter.setPen(QPen(QColor(0, 0, 0)))
        painter.drawText(QPointF(left_text_edge,
                                 inner_rect.top() + int(
                                     metrics.height() * 1.2)),
                         publisher.name())

        font.setBold(False)
        painter.setFont(font)
        painter.drawText(QPointF(left_text_edge,
                                 inner_rect.top() + int(
                                     metrics.height() * 2.1)),
                         'via ' + publisher.site.name())

        painter.setPen(QPen(QColor(0, 0, 0, 100)))
        painter.drawText(QPointF(left_text_edge,
                                 inner_rect.top() + int(
                                     metrics.height() * 3.0)),
                         '{} datasets '.format(DatasetGuiUtils.format_number(
                             publisher.dataset_count())))

        painter.restore()


class PublisherModel(QAbstractItemModel):
    """
    Qt model for publishers
    """

    TitleRole = Qt.UserRole + 1
    PublisherRole = Qt.UserRole + 2

    def __init__(self, parent: Optional[QObject] = None):
        super().__init__(parent)

        self.available_count = 0
        self.publishers: List[Publisher] = []
        self.current_page = 1
        self._load_next_results()

    def _load_next_results(self):
        self._current_reply = KoordinatesClient.instance().publishers_async(
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
                             len(self.publishers) + len(result))
        for p in result:
            self.publishers.append(Publisher(p))

        self.endInsertRows()

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

        self.setVerticalScrollMode(QAbstractItemView.ScrollPerPixel)


class PublisherFilterWidget(FilterWidgetComboBase):
    """
    Custom widget for publisher based filtering
    """

    def __init__(self, parent):
        super().__init__(parent)

        self.view = PublisherListView()
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
