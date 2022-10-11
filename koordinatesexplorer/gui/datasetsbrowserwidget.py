import json
import math
import os
from functools import partial
from typing import Optional

from dateutil import parser
from qgis.PyQt import sip
from qgis.PyQt.QtCore import Qt, pyqtSignal, QRect
from qgis.PyQt.QtGui import (
    QColor,
    QPixmap,
    QFont,
    QCursor,
    QPainter,
    QPainterPath,
    QImage,
    QBrush,
    QFontMetrics
)
from qgis.PyQt.QtNetwork import QNetworkReply
from qgis.PyQt.QtWidgets import (
    QTableWidget,
    QTableWidgetItem,
    QHBoxLayout,
    QFrame,
    QLabel,
    QToolButton,
    QVBoxLayout,
    QSizePolicy,
    QWidget
)
from qgis.core import Qgis
from qgis.core import (
    QgsProject,
    QgsGeometry,
    QgsWkbTypes,
    QgsCoordinateTransform,
    QgsCoordinateReferenceSystem,
    QgsFields,
    QgsJsonUtils,
)
from qgis.gui import QgsRubberBand
from qgis.utils import iface

from koordinatesexplorer.gui.datasetdialog import DatasetDialog
from koordinatesexplorer.gui.thumbnails import downloadThumbnail
from koordinatesexplorer.utils import cloneKartRepo, KartNotInstalledException
from ..api import (
    KoordinatesClient,
    PAGE_SIZE,
    DataBrowserQuery
)

pluginPath = os.path.split(os.path.dirname(__file__))[0]

COLOR_INDEX = 0


class Label(QLabel):
    def __init__(self):
        super(Label, self).__init__()
        self.setMaximumSize(150, 200)
        self.setMinimumSize(150, 200)


class DatasetsBrowserWidget(QTableWidget):
    datasetDetailsRequested = pyqtSignal(dict)
    total_count_changed = pyqtSignal(int)
    visible_count_changed = pyqtSignal(int)

    VERTICAL_SPACING = 10

    def __init__(self):
        super().__init__()
        self.itemClicked.connect(self._itemClicked)
        self.setSelectionMode(self.NoSelection)
        self.setColumnCount(1)
        self.horizontalHeader().hide()
        self.verticalHeader().hide()
        self.setColumnWidth(0, self.width())
        self.setShowGrid(False)
        #self.setSpacing(10)

        self.setObjectName('DatasetsBrowserWidget')
        self.setStyleSheet("""
        #DatasetsBrowserWidget {{ border: none; }}
        QTableWidget::item {{ padding-top: {}px }}
        """.format(self.VERTICAL_SPACING))
        self.viewport().setStyleSheet("#qt_scrollarea_viewport{ background: transparent; }")

        self._current_query: Optional[DataBrowserQuery] = None
        self._current_reply: Optional[QNetworkReply] = None
        self._current_context = None
        self._load_more_item = None
        self._no_records_item = None
        self._datasets = []
        self._temporary_blank_items = []

    def resizeEvent(self, event):
        super().resizeEvent(event)

        width_without_scroll_bar = self.width() - self.verticalScrollBar().width()
        col_count = int(width_without_scroll_bar / 450)
        col_count = max(1, col_count)
        self.reflow_cells(col_count)

        col_width = int(width_without_scroll_bar / self.columnCount())
        for i in range(self.columnCount()):
            self.setColumnWidth(i, col_width)

    def reflow_cells(self, col_count):
        if col_count == self.columnCount():
            return

        prev_columns = self.columnCount()
        prev_rows = self.rowCount()
        if col_count > self.columnCount():
            target_row = 0
            target_col = 0
            required_rows = 0
            self.setColumnCount(col_count)
            for row in range(prev_rows):
                for col in range(prev_columns):
                    widget = self.cellWidget(row,col)
                    if widget:
                        new_container = QWidget()
                        new_container.setLayout(widget.layout())
                        item = self.takeItem(row, col)
                        self.setItem(target_row, target_col, item)
                        self.setCellWidget(target_row, target_col, new_container)
                        required_rows = target_row
                        target_col += 1
                        if target_col == col_count:
                            target_col = 0
                            target_row += 1

            self.setRowCount(required_rows+1)
        else:
            # removing columns
            target_row = 0
            target_col = 0
            widget_count = 0

            items = []
            widgets = []
            remaps = {}
            for row in range(prev_rows):
                for col in range(prev_columns):
                    if self.cellWidget(row, col) and self.cellWidget(row, col).layout():
                        assert self.item(row, col)
                        items.append(self.item(row, col))
                        widgets.append(self.cellWidget(row, col))

                        remaps[widget_count] = (target_row, target_col)

                        widget_count += 1
                        target_col += 1
                        if target_col == col_count:
                            target_col = 0
                            target_row += 1

            self.setRowCount(remaps[len(widgets)-1][0] + 1)
            for row in range(self.rowCount()):
                self.setRowHeight(row,
                                  DatasetItemWidget.CARD_HEIGHT + self.VERTICAL_SPACING)

            for idx in range(len(widgets)-1, -1, -1):
                target_row, target_col = remaps[idx]
                widget = widgets[idx]
                item = items[idx]

                if item.row() == target_row and item.column() == target_col:
                    continue

                new_container = QWidget()
                new_container.setLayout(widget.layout())
                item = self.takeItem(item.row(), item.column())
                self.setItem(target_row, target_col, item)
                self.setCellWidget(target_row, target_col, new_container)

            self.setColumnCount(col_count)

        self.setColumnCount(col_count)

    def set_cell_widget_in_container(self, row, column, widget):
        container = QWidget()
        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.addWidget(widget)
        self.setCellWidget(row, column, container)

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
            datasetItem = QTableWidgetItem()
            datasetItem.setFlags(Qt.ItemFlags())
            datasetWidget = EmptyDatasetItemWidget()
            new_row = self.rowCount()
            self.setRowCount(new_row+1)
            self.setItem(new_row, 0, datasetItem)
            self.set_cell_widget_in_container(datasetItem.row(), datasetItem.column(), datasetWidget)
            self.setRowHeight(datasetItem.row(), DatasetItemWidget.CARD_HEIGHT + self.VERTICAL_SPACING)
            datasetItem.setSizeHint(datasetWidget.sizeHint())
            self._temporary_blank_items.append(datasetItem)

    def populate(self, query: DataBrowserQuery, context):
        self.clear()
        self.setRowCount(0)
        self._datasets = []
        self._temporary_blank_items = []
        self._create_temporary_items_for_page()

        self._load_more_item = None
        self._no_records_item = None

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

        prev_count = len(self._datasets)
        for i in self._temporary_blank_items:
            #self.removeRow(i.row())
            self.takeItem(i.row(), i.column())

        self._temporary_blank_items = []

        self.setRowCount(prev_count +len(datasets))
        self._add_datasets(datasets)
        self.setCursor(Qt.ArrowCursor)

        if not finished and not self._load_more_item:
            self._load_more_item = QTableWidgetItem()
            self._load_more_item.setFlags(Qt.ItemFlags())
            loadMoreWidget = LoadMoreItemWidget()
            loadMoreWidget.load_more.connect(self.load_more)
            new_row = self.rowCount()
            self.setRowCount(new_row+1)
            self.setItem(new_row, 0, self._load_more_item)
            self.set_cell_widget_in_container(self._load_more_item.row(), self._load_more_item.column(), loadMoreWidget)
            self.setRowHeight(self._load_more_item.row(), loadMoreWidget.sizeHint().height()+self.VERTICAL_SPACING)
            self._load_more_item.setSizeHint(loadMoreWidget.sizeHint())
        elif finished and self._load_more_item:
            self.takeItem(self.row(self._load_more_item))
            self._load_more_item = None

        if total == '0' and not self._no_records_item:
            self._no_records_item = QTableWidgetItem()
            self._no_records_item.setFlags(Qt.ItemFlags())
            no_records_widget = NoRecordsItemWidget()
            new_row = self.rowCount()
            self.setRowCount(new_row + 1)
            self.setItem(new_row, 0, self._no_records_item)
            self.set_cell_widget_in_container(self._no_records_item.row(), self._no_records_item.column(), no_records_widget)
            self.setRowHeight(self._no_records_item.row(), no_records_widget.sizeHint().height()+self.VERTICAL_SPACING)
        elif total != '0' and self._no_records_item:
            self.takeItem(self.row(self._no_records_item))
            self._no_records_item = None

        self._datasets.extend(datasets)

    def _add_datasets(self, datasets):
        for i, dataset in enumerate(datasets):
            datasetItem = QTableWidgetItem()
            datasetItem.setFlags(Qt.ItemFlags())
            datasetWidget = DatasetItemWidget(dataset)
            new_row = len(self._datasets) + i
            if self.rowCount() < new_row + 1:
                self.setRowCount(new_row+1)

            self.setItem(new_row, 0, datasetItem)
            self.set_cell_widget_in_container(datasetItem.row(), datasetItem.column(), datasetWidget)
            self.setRowHeight(datasetItem.row(), DatasetItemWidget.CARD_HEIGHT+ self.VERTICAL_SPACING)
            datasetItem.setSizeHint(datasetWidget.sizeHint())
        self.visible_count_changed.emit(self.rowCount() - (1 if self._load_more_item else 0))

    def _itemClicked(self, item):
        widget = self.cellWidget(item.row(), item.column())
        if isinstance(widget, DatasetItemWidget):
            widget.showDetails()

    def load_more(self):
        next_page = math.ceil(self.rowCount() / PAGE_SIZE)
        self.removeRow(self._load_more_item.row())
        self._load_more_item = None
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


class DatasetItemWidgetBase(QFrame):
    """
    Base class for dataset items
    """

    def __init__(self):
        super().__init__()
        self.setStyleSheet(
            """DatasetItemWidgetBase {
               border: 0px solid black;
               border-radius: 10px; background: white;
            }"""
        )
        self.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Fixed)

        self.labelMap = Label()
        self.labelMap.setFixedSize(150, 150)

        self.labelName = QLabel()
        self.labelName.setFont(QFont("Arial", 10))
        self.labelName.setWordWrap(True)

        self.stats_hlayout = QHBoxLayout()

        self.vlayout = QVBoxLayout()
        self.vlayout.addWidget(self.labelName)
        self.vlayout.addLayout(self.stats_hlayout)

        layout = QHBoxLayout()
        layout.setMargin(0)
        layout.addWidget(self.labelMap)
        layout.addLayout(self.vlayout)

        self.buttonsLayout = QVBoxLayout()

        layout.addLayout(self.buttonsLayout)
        layout.addSpacing(20)

        self.setLayout(layout)

    def setThumbnail(self, img: Optional[QImage]):

        target = QPixmap(self.labelMap.size())
        target.fill(Qt.transparent)

        painter = QPainter(target)

        painter.setRenderHint(QPainter.Antialiasing, True)
        painter.setRenderHint(QPainter.HighQualityAntialiasing, True)
        painter.setRenderHint(QPainter.SmoothPixmapTransform, True)

        path = QPainterPath()
        path.addRoundedRect(0, 0, 150, 150, 10, 10)

        painter.setClipPath(path)

        if img is not None:
            rect = QRect(300, 15, 600, 600)
            thumbnail = QPixmap(img)
            cropped = thumbnail.copy(rect)

            thumb = cropped.scaled(
                150, 150, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation
            )
            painter.drawPixmap(0, 0, thumb)
        else:
            painter.setBrush(QBrush(QColor('#cccccc')))
            painter.setPen(Qt.NoPen)
            painter.drawRect(0, 0, 600, 600)

        painter.end()

        self.labelMap.setPixmap(target)


class EmptyDatasetItemWidget(DatasetItemWidgetBase):
    """
    Shows an 'empty' dataset item
    """

    TOP_LABEL_HEIGHT = 40
    TOP_LABEL_MARGIN = 15
    TOP_LABEL_WIDTH = 300
    BOTTOM_LABEL_HEIGHT = 20
    BOTTOM_LABEL_MARGIN = 40
    BOTTOM_LABEL_WIDTH = 130

    def __init__(self):
        super().__init__()

        self.setThumbnail(None)

        target = QPixmap(self.TOP_LABEL_WIDTH,
                         self.TOP_LABEL_HEIGHT + self.TOP_LABEL_MARGIN)
        target.fill(Qt.transparent)

        painter = QPainter(target)

        painter.setRenderHint(QPainter.Antialiasing, True)
        painter.setRenderHint(QPainter.HighQualityAntialiasing, True)

        painter.setBrush(QBrush(QColor('#e6e6e6')))
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(0, self.TOP_LABEL_MARGIN,
                                self.TOP_LABEL_WIDTH, self.TOP_LABEL_HEIGHT,
                                4, 4)

        painter.end()

        self.labelName.setPixmap(target)
        self.vlayout.addStretch()

        target = QPixmap(self.BOTTOM_LABEL_WIDTH,
                         self.BOTTOM_LABEL_HEIGHT + self.BOTTOM_LABEL_MARGIN)
        target.fill(Qt.transparent)

        painter = QPainter(target)

        painter.setRenderHint(QPainter.Antialiasing, True)
        painter.setRenderHint(QPainter.HighQualityAntialiasing, True)

        painter.setBrush(QBrush(QColor('#e6e6e6')))
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(0,
                                self.BOTTOM_LABEL_MARGIN,
                                self.BOTTOM_LABEL_WIDTH,
                                self.BOTTOM_LABEL_HEIGHT,
                                4,
                                4)

        painter.end()

        bottom_label = QLabel()
        bottom_label.setPixmap(target)
        self.stats_hlayout.addWidget(bottom_label)
        self.stats_hlayout.addStretch()


class DatasetItemWidget(DatasetItemWidgetBase):
    """
    Shows details for a dataset item
    """

    CARD_HEIGHT = 152

    def __init__(self, dataset):
        super().__init__()
        self.setMouseTracking(True)
        self.dataset = dataset

        if self.dataset.get('thumbnail_url'):
            downloadThumbnail(self.dataset["thumbnail_url"], self)

        date = parser.parse(self.dataset["published_at"])

        def mousePressed(event):
            self.showDetails()

        self.labelName.mousePressEvent = mousePressed

        self.labelName.setText(
            f'<b>{self.dataset["title"]}</b><br>'
            f'{self.dataset["publisher"]["name"]}<br>'
        )

        def pixmap(name):
            return QPixmap(
                os.path.join(os.path.dirname(os.path.dirname(__file__)), "img", name)
            )

        self.labelUpdatedIcon = QLabel()
        self.labelUpdatedIcon.setPixmap(pixmap("updated.png"))

        self.labelUpdated = QLabel()

        self.labelViewsIcon = QLabel()
        self.labelViewsIcon.setPixmap(pixmap("eye.png"))

        self.labelViews = QLabel()

        self.labelExportsIcon = QLabel()
        self.labelExportsIcon.setPixmap(pixmap("download.png"))

        self.labelExports = QLabel()

        self.labelUpdated.setText(f'{date.strftime("%d %b %Y")}')

        self.labelViews.setText(str(self.dataset["num_views"]))

        self.labelExports.setText(str(self.dataset["num_downloads"]))

        self.stats_hlayout.addWidget(self.labelUpdatedIcon)
        self.stats_hlayout.addWidget(self.labelUpdated)
        self.stats_hlayout.addWidget(self.labelViewsIcon)
        self.stats_hlayout.addWidget(self.labelViews)
        self.stats_hlayout.addWidget(self.labelExportsIcon)
        self.stats_hlayout.addWidget(self.labelExports)
        self.stats_hlayout.addStretch()

        style = """
                QToolButton{
                background-color: #1b9a4b;
                border-style: outset;
                border-width: 1px;
                border-radius: 4px;
                border-color: rgb(150, 150, 150);
                font: bold 14px;
                color: white;
                padding: 5px 0px 5px 0px;
                }
                QToolButton:hover{
                    background-color: #119141;
                }
                """

        self.buttonsLayout.addStretch()

        if self.dataset.get("repository") is not None:
            self.btnClone = QToolButton()
            self.btnClone.setText("Clone")
            self.btnClone.setStyleSheet(style)
            self.btnClone.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Maximum)
            self.btnClone.clicked.connect(self.cloneRepository)
            self.btnClone.setFixedSize(80, 40)
            self.buttonsLayout.addWidget(self.btnClone)

        if self.dataset.get("kind") in ["raster", "vector"]:
            self.btnAdd = QToolButton()
            self.btnAdd.setText("+Add")
            self.btnAdd.setStyleSheet(style)
            self.btnAdd.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Maximum)
            self.btnAdd.clicked.connect(self.addLayer)
            self.btnAdd.setFixedSize(80, 40)
            self.buttonsLayout.addWidget(self.btnAdd)

        self.buttonsLayout.addSpacing(10)

        self.bbox = self._geomFromGeoJson(self.dataset["data"].get("extent"))
        self.footprint = QgsRubberBand(iface.mapCanvas(), QgsWkbTypes.PolygonGeometry)
        self.footprint.setWidth(2)
        self.footprint.setColor(QColor(255, 0, 0, 200))
        self.footprint.setFillColor(QColor(255, 0, 0, 40))

        self.setCursor(QCursor(Qt.PointingHandCursor))

    def cloneRepository(self):
        url = self.dataset["repository"]["clone_location_https"]
        try:
            if cloneKartRepo(
                    url, "kart", KoordinatesClient.instance().apiKey, iface.mainWindow()
            ):
                iface.messageBar().pushMessage(
                    "Repository correctly cloned", Qgis.Info, duration=5
                )
        except KartNotInstalledException:
            iface.messageBar().pushMessage(
                "Kart plugin must be installed to clone repositories",
                Qgis.Warning,
                duration=5,
            )

    def addLayer(self):
        MAP_LAYER_COLORS = (
            "003399",
            "ff0000",
            "009e00",
            "ff7b00",
            "ff0090",
            "9900ff",
            "6b6b6b",
            "ff7e7e",
            "d4c021",
            "00cf9f",
            "81331f",
            "7ca6ff",
            "82d138",
            "32c8db",
        )

        global COLOR_INDEX
        color = MAP_LAYER_COLORS[COLOR_INDEX % len(MAP_LAYER_COLORS)]
        COLOR_INDEX += 1

        apikey = KoordinatesClient.instance().apiKey
        uri = (
            f"type=xyz&url=https://tiles-a.koordinates.com/services;key%3D{apikey}/tiles/v4/"
            f"layer={self.dataset['id']},color={color}/EPSG:3857/"
            "%7BZ%7D/%7BX%7D/%7BY%7D.png&zmax=19&zmin=0&crs=EPSG3857"
        )
        iface.addRasterLayer(uri, self.dataset["title"], "wms")

    def showDetails(self):
        dataset = (
            self.dataset
        )  # KoordinatesClient.instance().dataset(self.dataset["id"])
        dlg = DatasetDialog(dataset)
        dlg.exec()

    def _geomFromGeoJson(self, geojson):
        try:
            feats = QgsJsonUtils.stringToFeatureList(
                json.dumps(geojson), QgsFields(), None
            )
            geom = feats[0].geometry()
        except Exception:
            geom = QgsGeometry()

        return geom

    def enterEvent(self, event):
        self.setStyleSheet(
            """DatasetItemWidget {
               border: 1px solid rgb(180, 180, 180);
               border-radius: 15px;
               background: white;
            }"""
        )
        self.showFootprint()

    def leaveEvent(self, event):
        self.setStyleSheet(
            """DatasetItemWidget {
                border: 1px solid transparent;
                border-radius: 15px;
                background: white;
            }"""
        )
        self.hideFootprint()

    def _bboxInProjectCrs(self):
        geom = QgsGeometry(self.bbox)
        transform = QgsCoordinateTransform(
            QgsCoordinateReferenceSystem("EPSG:4326"),
            QgsProject.instance().crs(),
            QgsProject.instance(),
        )
        geom.transform(transform)
        return geom

    def showFootprint(self):
        if self.bbox is not None:
            self.footprint.setToGeometry(self._bboxInProjectCrs())

    def hideFootprint(self):
        self.footprint.reset(QgsWkbTypes.PolygonGeometry)

    def zoomToBoundingBox(self):
        rect = self.bbox.boundingBox()
        rect.scale(1.05)
        iface.mapCanvas().setExtent(rect)
        iface.mapCanvas().refresh()
