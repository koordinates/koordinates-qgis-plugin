import os
import json
import math
from dateutil import parser

from qgis.core import Qgis
from qgis.PyQt.QtCore import Qt, pyqtSignal, QRect
from qgis.PyQt.QtGui import QColor, QPixmap, QFont, QCursor, QPainter, QPainterPath

from qgis.PyQt.QtWidgets import (
    QListWidget,
    QListWidgetItem,
    QHBoxLayout,
    QFrame,
    QLabel,
    QToolButton,
    QVBoxLayout,
    QSizePolicy,
)

from qgis.gui import QgsRubberBand
from qgis.utils import iface
from qgis.core import (
    QgsProject,
    QgsGeometry,
    QgsWkbTypes,
    QgsCoordinateTransform,
    QgsCoordinateReferenceSystem,
    QgsFields,
    QgsJsonUtils,
)

from ..api import KoordinatesClient, PAGE_SIZE
from koordinatesexplorer.gui.datasetdialog import DatasetDialog
from koordinatesexplorer.gui.thumbnails import downloadThumbnail
from koordinatesexplorer.utils import cloneKartRepo, KartNotInstalledException

pluginPath = os.path.split(os.path.dirname(__file__))[0]

COLOR_INDEX = 0


class Label(QLabel):
    def __init__(self):
        super(Label, self).__init__()
        self.setMaximumSize(150, 200)
        self.setMinimumSize(150, 200)


class DatasetsBrowserWidget(QListWidget):

    datasetDetailsRequested = pyqtSignal(dict)

    def __init__(self):
        QListWidget.__init__(self)
        self.itemClicked.connect(self._itemClicked)
        self.setSelectionMode(self.NoSelection)
        self.setSpacing(10)
        self.setStyleSheet("""QListWidget{background: #E5E7E9;}""")

    def populate(self, params, context):
        self.clear()
        datasets, finished = KoordinatesClient.instance().datasets(
            params=params, context=context
        )
        for dataset in datasets:
            datasetItem = QListWidgetItem()
            datasetWidget = DatasetItemWidget(dataset)
            self.addItem(datasetItem)
            self.setItemWidget(datasetItem, datasetWidget)
            datasetItem.setSizeHint(datasetWidget.sizeHint())
        if not finished:
            loadMoreItem = QListWidgetItem()
            loadMoreWidget = LoadMoreItemWidget(self, params)
            self.addItem(loadMoreItem)
            self.setItemWidget(loadMoreItem, loadMoreWidget)
            loadMoreItem.setSizeHint(loadMoreWidget.sizeHint())

    def _itemClicked(self, item):
        widget = self.itemWidget(item)
        if isinstance(widget, DatasetItemWidget):
            widget.showDetails()


class LoadMoreItemWidget(QFrame):
    def __init__(self, listWidget, params):
        QFrame.__init__(self)
        self.listWidget = listWidget
        self.params = params
        self.btnLoadMore = QToolButton()
        self.btnLoadMore.setText("Load more...")
        self.btnLoadMore.clicked.connect(self.loadMore)

        layout = QHBoxLayout()
        layout.addStretch()
        layout.addWidget(self.btnLoadMore)
        layout.addStretch()
        self.setLayout(layout)

    def loadMore(self):
        page = math.ceil(self.listWidget.count() / PAGE_SIZE)
        datasets, finished = KoordinatesClient.instance().datasets(
            page=page, params=self.params
        )
        for dataset in datasets:
            datasetItem = QListWidgetItem()
            datasetWidget = DatasetItemWidget(dataset)
            self.listWidget.insertItem(self.listWidget.count() - 1, datasetItem)
            self.listWidget.setItemWidget(datasetItem, datasetWidget)
            datasetItem.setSizeHint(datasetWidget.sizeHint())
        if finished:
            self.listWidget.takeItem(self.listWidget.count())


class DatasetItemWidget(QFrame):
    def __init__(self, dataset):
        QFrame.__init__(self)
        self.setMouseTracking(True)
        self.setStyleSheet(
            "DatasetItemWidget{border: 0px solid black; border-radius: 10px; background: white;}"
        )
        self.dataset = dataset

        self.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Fixed)

        def pixmap(name):
            return QPixmap(
                os.path.join(os.path.dirname(os.path.dirname(__file__)), "img", name)
            )

        self.labelMap = Label()
        self.labelMap.setFixedSize(150, 150)
        downloadThumbnail(self.dataset["thumbnail_url"], self)

        date = parser.parse(self.dataset["published_at"])
        self.labelName = QLabel(
            f'<b>{self.dataset["title"]}</b><br>'
            f'{self.dataset["publisher"]["name"]}<br>'
        )
        self.labelName.setFont(QFont("Arial", 10))
        self.labelName.setWordWrap(True)

        def mousePressed(event):
            self.showDetails()

        self.labelName.mousePressEvent = mousePressed

        self.labelUpdatedIcon = QLabel()
        self.labelUpdatedIcon.setPixmap(pixmap("updated.png"))
        self.labelUpdated = QLabel(f'{date.strftime("%d %b %Y")}')
        self.labelViewsIcon = QLabel()
        self.labelViewsIcon.setPixmap(pixmap("eye.png"))
        self.labelViews = QLabel(str(self.dataset["num_views"]))
        self.labelExportsIcon = QLabel()
        self.labelExportsIcon.setPixmap(pixmap("download.png"))
        self.labelExports = QLabel(str(self.dataset["num_downloads"]))

        hlayout = QHBoxLayout()
        hlayout.addWidget(self.labelUpdatedIcon)
        hlayout.addWidget(self.labelUpdated)
        hlayout.addWidget(self.labelViewsIcon)
        hlayout.addWidget(self.labelViews)
        hlayout.addWidget(self.labelExportsIcon)
        hlayout.addWidget(self.labelExports)
        hlayout.addStretch()

        vlayout = QVBoxLayout()
        vlayout.addWidget(self.labelName)
        vlayout.addLayout(hlayout)

        layout = QHBoxLayout()
        layout.setMargin(0)
        layout.addWidget(self.labelMap)
        layout.addLayout(vlayout)

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

        buttonsLayout = QVBoxLayout()
        buttonsLayout.addStretch()

        if self.dataset.get("repository") is not None:
            self.btnClone = QToolButton()
            self.btnClone.setText("Clone")
            self.btnClone.setStyleSheet(style)
            self.btnClone.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Maximum)
            self.btnClone.clicked.connect(self.cloneRepository)
            self.btnClone.setFixedSize(80, 40)
            buttonsLayout.addWidget(self.btnClone)

        if self.dataset.get("kind") in ["raster", "vector"]:
            self.btnAdd = QToolButton()
            self.btnAdd.setText("+Add")
            self.btnAdd.setStyleSheet(style)
            self.btnAdd.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Maximum)
            self.btnAdd.clicked.connect(self.addLayer)
            self.btnAdd.setFixedSize(80, 40)
            buttonsLayout.addWidget(self.btnAdd)

        buttonsLayout.addSpacing(10)
        layout.addLayout(buttonsLayout)
        layout.addSpacing(20)

        self.setLayout(layout)

        self.bbox = self._geomFromGeoJson(self.dataset["data"].get("extent"))
        self.footprint = QgsRubberBand(iface.mapCanvas(), QgsWkbTypes.PolygonGeometry)
        self.footprint.setWidth(2)
        self.footprint.setColor(QColor(255, 0, 0, 200))
        self.footprint.setFillColor(QColor(255, 0, 0, 40))

        self.setCursor(QCursor(Qt.PointingHandCursor))

    def setThumbnail(self, img):
        thumbnail = QPixmap(img)

        rect = QRect(300, 15, 600, 600)
        cropped = thumbnail.copy(rect)

        thumb = cropped.scaled(
            150, 150, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation
        )

        self.target = QPixmap(self.labelMap.size())
        self.target.fill(Qt.transparent)

        painter = QPainter(self.target)

        painter.setRenderHint(QPainter.Antialiasing, True)
        painter.setRenderHint(QPainter.HighQualityAntialiasing, True)
        painter.setRenderHint(QPainter.SmoothPixmapTransform, True)

        path = QPainterPath()
        path.addRoundedRect(0, 0, 150, 150, 10, 10)

        painter.setClipPath(path)
        painter.drawPixmap(0, 0, thumb)
        self.labelMap.setPixmap(self.target)

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
            f"layer={self.dataset['id']},color={color}/EPSG:3857/%7BZ%7D/%7BX%7D/%7BY%7D.png&zmax=19&zmin=0&crs=EPSG3857"  # noqa: E501
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
            "DatasetItemWidget{border: 1px solid rgb(180, 180, 180); border-radius: 15px; background: white;}"  # noqa: E501
        )
        self.showFootprint()

    def leaveEvent(self, event):
        self.setStyleSheet(
            "DatasetItemWidget{border: 0px solid black; border-radius: 15px; background: white;}"
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
