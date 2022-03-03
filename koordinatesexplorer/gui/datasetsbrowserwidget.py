import os
import json
import requests
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
    QMenu,
    QDialog,
    QVBoxLayout,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView
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
    Qgis,
    QgsMessageLog,
)

from koordinatesexplorer.client import KoordinatesClient
from koordinatesexplorer.gui.datasetdialog import DatasetDialog

pluginPath = os.path.split(os.path.dirname(__file__))[0]


class DatasetsBrowserWidget(QListWidget):

    datasetDetailsRequested = pyqtSignal(dict)

    def populate(self):
        self.clear()
        datasets = KoordinatesClient.instance().datasets()
        for dataset in datasets[1:40]:
            datasetItem = QListWidgetItem()
            datasetWidget = DatasetItemWidget(dataset)
            self.addItem(datasetItem)
            self.setItemWidget(datasetItem, datasetWidget)
            datasetItem.setSizeHint(datasetWidget.sizeHint())
            datasetWidget.datasetDetailsRequested.connect(self._datasetDetailsRequested)

    def _datasetDetailsRequested(self, dataset):
        self.datasetDetailsRequested.emit(dataset)


class DatasetItemWidget(QFrame):

    datasetDetailsRequested = pyqtSignal(dict)

    def __init__(self, dataset):
        QFrame.__init__(self)
        self.setMouseTracking(True)
        self.setStyleSheet("DatasetItemWidget{border: 2px solid transparent;}")
        self.dataset = KoordinatesClient.instance().dataset(dataset["id"])

        path = f"c:\\temp\\{dataset['id']}.png"
        '''
        r = requests.get(self.dataset["thumbnail_url"], stream=True)
        with open(path, 'wb') as f:
            for chunk in r.iter_content():
                f.write(chunk)
        '''

        def pixmap(name):
            return QPixmap(os.path.join(os.path.dirname(os.path.dirname(__file__)), "img", name))

        thumbnail = QPixmap(path)
        thumb = thumbnail.scaled(
            120, 63, Qt.KeepAspectRatio, Qt.SmoothTransformation
        )
        self.iconLabel = QLabel()
        self.iconLabel.setPixmap(thumb)
        self.iconLabel.setFixedSize(120, 63)

        date = parser.parse(self.dataset["published_at"])
        self.labelName = QLabel()
        self.labelName.setFont(QFont('Arial', 10))
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

        self.btnDetails = QToolButton()
        self.btnDetails.setText("Details")
        self.btnDetails.clicked.connect(self.showDetails)

        layout = QHBoxLayout()
        layout.addWidget(self.iconLabel)
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

    def addLayer(self):
        apikey = KoordinatesClient.instance().apiKey
        uri = (
            "contextualWMSLegend=0&crs=EPSG:3857&dpiMode=7&featureCount=10&format=image/png&layers=layer-"
            f"{self.dataset['id']}&styles=style%3Dauto&tileMatrixSet=EPSG:3857&"
            f"url=https://koordinates.com/services;key%3D{apikey}/wmts/1.0.0/layer/{self.dataset['id']}/WMTSCapabilities.xml"
        )
        iface.addRasterLayer(uri, self.dataset["title"], "wms")

    def showDetails(self):
        dlg = DatasetDialog(self.dataset)
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

    def showProperties(self):
        dialog = QDialog()
        dialog.setWindowTitle("Dataset properties")
        layout = QVBoxLayout()
        table = QTableWidget()

        table.setRowCount(len(self.dataset))
        table.setColumnCount(2)
        table.setHorizontalHeaderLabels(["Property", "Value"])

        for i, key in enumerate(self.dataset):
            table.setItem(i, 0, QTableWidgetItem(str(key)))
            table.setItem(i, 1, QTableWidgetItem(str(self.dataset[key])))

        table.horizontalHeader().setStretchLastSection(True)
        table.horizontalHeader().setSectionResizeMode(
            QHeaderView.Stretch)
        table.verticalHeader().hide()

        layout.addWidget(table)
        dialog.setLayout(layout)
        dialog.exec()


class PointsDatasetItemWidget(DatasetItemWidget):
    def __init__(self, dataset, username):
        DatasetItemWidget.__init__(self, dataset)
        self.username = username
        self.labelName.setText(
            f'<b>{dataset["datasetname"].upper()}</b><br>'
            f'{dataset["date"] or "N/A"}<br>'
            f'{dataset["count"]} points'
        )

        self.menu = QMenu()
        self.actionDownload = self.menu.addAction("Download full dataset")
        self.actionDownload.triggered.connect(self.download)
        self.actionDownloadFiltered = self.menu.addAction(
            "Download dataset filtered with current extent"
        )
        self.actionDownloadFiltered.triggered.connect(self.downloadFiltered)
        self.menu.addSeparator()
        self.actionZoom = self.menu.addAction("Zoom to dataset")
        self.actionZoom.triggered.connect(self.zoomToBoundingBox)
        self.menu.addSeparator()
        self.actionShowProperties = self.menu.addAction("Show properties")
        self.actionShowProperties.triggered.connect(self.showProperties)

        self.btnAdd.setMenu(self.menu)
        self.btnAdd.clicked.connect(self.btnAdd.showMenu)

    def download(self):
        self._download(False)

    def downloadFiltered(self):
        self._download(True)

    def _download(self, filtered):
        try:
            if filtered:
                ext = iface.mapCanvas().extent()
                bbox = ",".join(
                    [
                        str(v)
                        for v in [
                            ext.xMinimum(),
                            ext.xMaximum(),
                            ext.yMinimum(),
                            ext.yMaximum(),
                        ]
                    ]
                )
                geojson = self._downloadGeoJson(bbox)
            else:
                geojson = self._downloadGeoJson()
            self._addLayer(geojson)
        except Exception as e:
            QgsMessageLog.logMessage(
                f"Dataset '{self.dataset['datasetname']}' could not be"
                f" downloaded.\n{e}",
                "Detektia",
                Qgis.Warning,
            )
            iface.messageBar().pushMessage(
                "Detektia",
                f"Dataset '{self.dataset['datasetname']}' could not be downloaded. See log for"
                " details",
                level=Qgis.Warning,
                duration=5,
            )

    def _downloadGeoJson(self, bbox=None):
        return DetektiaClient.instance().downloadPoints(
            self.dataset["datasetname"], self.username, bbox
        )

