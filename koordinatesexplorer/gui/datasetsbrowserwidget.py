import os
import json
import math
from dateutil import parser

from qgis.PyQt.QtCore import Qt, pyqtSignal
from qgis.PyQt.QtGui import QColor, QPixmap, QFont
from qgis.PyQt.QtWidgets import (
    QListWidget,
    QListWidgetItem,
    QHBoxLayout,
    QFrame,
    QLabel,
    QToolButton,
    QVBoxLayout,
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

pluginPath = os.path.split(os.path.dirname(__file__))[0]


class DatasetsBrowserWidget(QListWidget):

    datasetDetailsRequested = pyqtSignal(dict)

    def populate(self):
        self.clear()
        datasets = KoordinatesClient.instance().datasets()
        for dataset in datasets:
            datasetItem = QListWidgetItem()
            datasetWidget = DatasetItemWidget(dataset)
            self.addItem(datasetItem)
            self.setItemWidget(datasetItem, datasetWidget)
            datasetItem.setSizeHint(datasetWidget.sizeHint())
        loadMoreItem = QListWidgetItem()
        loadMoreWidget = LoadMoreItemWidget(self)
        self.addItem(loadMoreItem)
        self.setItemWidget(loadMoreItem, loadMoreWidget)
        loadMoreItem.setSizeHint(loadMoreWidget.sizeHint())


class LoadMoreItemWidget(QFrame):
    def __init__(self, listWidget):
        QFrame.__init__(self)
        self.listWidget = listWidget
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
        datasets = KoordinatesClient.instance().datasets(page=page)
        for dataset in datasets:
            datasetItem = QListWidgetItem()
            datasetWidget = DatasetItemWidget(dataset)
            self.listWidget.insertItem(self.listWidget.count() - 1, datasetItem)
            self.listWidget.setItemWidget(datasetItem, datasetWidget)
            datasetItem.setSizeHint(datasetWidget.sizeHint())


class DatasetItemWidget(QFrame):
    def __init__(self, dataset):
        QFrame.__init__(self)
        self.setMouseTracking(True)
        self.setStyleSheet("DatasetItemWidget{border: 2px solid transparent;}")
        self.dataset = dataset

        def pixmap(name):
            return QPixmap(os.path.join(os.path.dirname(os.path.dirname(__file__)), "img", name))

        self.labelMap = QLabel()
        self.labelMap.setFixedSize(120, 63)
        downloadThumbnail(self.dataset["thumbnail_url"], self)

        date = parser.parse(self.dataset["published_at"])
        self.labelName = QLabel()
        self.labelName.setFont(QFont('Arial', 10))
        self.labelName.setWordWrap(True)
        self.labelName.setText(
            f'<b>{self.dataset["title"].upper()}</b><br>'
        )
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
        self.btnAdd.clicked.connect(self.addLayer)
        self.btnAdd.setEnabled(self.dataset["kind"] == "raster")

        self.btnDetails = QToolButton()
        self.btnDetails.setText("Details")
        self.btnDetails.clicked.connect(self.showDetails)

        layout = QHBoxLayout()
        layout.addWidget(self.labelMap)
        layout.addLayout(vlayout)
        layout.addStretch()
        layout.addWidget(self.btnAdd)
        layout.addWidget(self.btnDetails)
        self.setLayout(layout)

        self.bbox = self._geomFromGeoJson(self.dataset["data"]["extent"])
        self.footprint = QgsRubberBand(iface.mapCanvas(), QgsWkbTypes.PolygonGeometry)
        self.footprint.setWidth(2)
        self.footprint.setColor(QColor(255, 0, 0, 200))
        self.footprint.setFillColor(QColor(255, 0, 0, 40))

    def setThumbnail(self, img):
        thumbnail = QPixmap(img)
        thumb = thumbnail.scaled(
            120, 63, Qt.KeepAspectRatio, Qt.SmoothTransformation
        )
        self.labelMap.setPixmap(thumb)

    def addLayer(self):
        apikey = KoordinatesClient.instance().apiKey
        uri = (
            "contextualWMSLegend=0&crs=EPSG:3857&dpiMode=7&featureCount=10&format=image/png&layers=layer-"
            f"{self.dataset['id']}&styles=style%3Dauto&tileMatrixSet=EPSG:3857&"
            f"url=https://koordinates.com/services;key%3D{apikey}/wmts/1.0.0/layer/{self.dataset['id']}/WMTSCapabilities.xml"
        )
        iface.addRasterLayer(uri, self.dataset["title"], "wms")

    def showDetails(self):
        dataset = KoordinatesClient.instance().dataset(self.dataset["id"])
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
        self.footprint.setToGeometry(self._bboxInProjectCrs())

    def hideFootprint(self):
        self.footprint.reset(QgsWkbTypes.PolygonGeometry)

    def zoomToBoundingBox(self):
        rect = self.bbox.boundingBox()
        rect.scale(1.05)
        iface.mapCanvas().setExtent(rect)
        iface.mapCanvas().refresh()
