import os
import json
import math
from dateutil import parser

from qgis.core import Qgis
from qgis.PyQt.QtCore import Qt, pyqtSignal
from qgis.PyQt.QtGui import QColor, QPixmap, QFont, QCursor
from qgis.PyQt.QtWidgets import (
    QListWidget,
    QListWidgetItem,
    QHBoxLayout,
    QFrame,
    QLabel,
    QToolButton,
    QVBoxLayout,
    QMenu,
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

from koordinatesexplorer.client import KoordinatesClient, PAGE_SIZE
from koordinatesexplorer.gui.datasetdialog import DatasetDialog
from koordinatesexplorer.gui.thumbnails import downloadThumbnail
from koordinatesexplorer.utils import cloneKartRepo, KartNotInstalledException

pluginPath = os.path.split(os.path.dirname(__file__))[0]


class DatasetsBrowserWidget(QListWidget):

    datasetDetailsRequested = pyqtSignal(dict)

    def __init__(self):
        QListWidget.__init__(self)
        self.itemClicked.connect(self._itemClicked)
        self.setSelectionMode(self.NoSelection)

    def populate(self, params):
        self.clear()
        datasets, finished = KoordinatesClient.instance().datasets(params=params)
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
        self.setStyleSheet("DatasetItemWidget{border: 2px solid transparent;}")
        self.dataset = dataset

        self.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Fixed)

        def pixmap(name):
            return QPixmap(
                os.path.join(os.path.dirname(os.path.dirname(__file__)), "img", name)
            )

        self.labelMap = QLabel()
        self.labelMap.setFixedSize(120, 63)
        downloadThumbnail(self.dataset["thumbnail_url"], self)

        date = parser.parse(self.dataset["published_at"])
        self.labelName = QLabel(f'<b>{self.dataset["title"].upper()}</b><br>')
        self.labelName.setFont(QFont("Arial", 10))
        self.labelName.setWordWrap(True)

        def mousePressed(event):
            self.showDetails()

        self.labelName.mousePressEvent = mousePressed

        self.labelUpdatedIcon = QLabel()
        self.labelUpdatedIcon.setPixmap(pixmap("updated.png"))
        self.labelUpdated = QLabel(f'{date.strftime("%d, %b %Y")}')
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

        self.btnAdd = QToolButton()
        self.btnAdd.setText("+Add")
        self.btnAdd.setStyleSheet(
            """
                background-color: rgb(255, 255, 255);
                border-style: outset;
                border-width: 2px;
                border-radius: 10px;
                border-color: black;
                font: bold 14px;
                padding: 20px;
                """
        )
        self.btnAdd.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Maximum)

        self.menu = QMenu()
        if self.dataset.get("kind") == "raster":
            self.actionWmts = self.menu.addAction("WMTS layer")
            self.actionWmts.triggered.connect(self.addLayer)
        if self.dataset.get("repository") is not None:
            self.actionClone = self.menu.addAction("Clone repository")
            self.actionClone.triggered.connect(self.cloneRepository)

        if self.menu.actions():
            self.btnAdd.setMenu(self.menu)
            self.btnAdd.clicked.connect(self.btnAdd.showMenu)
            self.btnAdd.setEnabled(True)
        else:
            self.btnAdd.setEnabled(False)

        layout = QHBoxLayout()
        layout.addWidget(self.labelMap)
        layout.addLayout(vlayout)
        layout.addWidget(self.btnAdd)
        self.setLayout(layout)

        self.bbox = self._geomFromGeoJson(self.dataset["data"].get("extent"))
        self.footprint = QgsRubberBand(iface.mapCanvas(), QgsWkbTypes.PolygonGeometry)
        self.footprint.setWidth(2)
        self.footprint.setColor(QColor(255, 0, 0, 200))
        self.footprint.setFillColor(QColor(255, 0, 0, 40))

        self.setCursor(QCursor(Qt.PointingHandCursor))

    def setThumbnail(self, img):
        thumbnail = QPixmap(img)
        thumb = thumbnail.scaled(120, 63, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.labelMap.setPixmap(thumb)

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
        apikey = KoordinatesClient.instance().apiKey
        uri = (
            "contextualWMSLegend=0&crs=EPSG:3857&dpiMode=7&featureCount=10&format=image/png&layers=layer-"
            f"{self.dataset['id']}&styles=style%3Dauto&tileMatrixSet=EPSG:3857&"
            f"url=https://koordinates.com/services;key%3D{apikey}/wmts/1.0.0/layer/{self.dataset['id']}/WMTSCapabilities.xml"
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
        self.setStyleSheet("DatasetItemWidget{border: 2px solid rgb(180, 180, 180);}")
        self.showFootprint()

    def leaveEvent(self, event):
        self.setStyleSheet("DatasetItemWidget{border: 2px solid transparent;}")
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
