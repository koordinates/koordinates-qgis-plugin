import os
from dateutil import parser

from qgis.utils import iface

from qgis.PyQt import uic
from qgis.PyQt.QtCore import Qt
from qgis.PyQt.QtGui import QPixmap
from qgis.PyQt.QtWidgets import QDialog

from koordinatesexplorer.gui.thumbnails import downloadThumbnail

pluginPath = os.path.split(os.path.dirname(__file__))[0]

WIDGET, BASE = uic.loadUiType(
    os.path.join(os.path.dirname(__file__), "datasetdialog.ui")
)


class DatasetDialog(BASE, WIDGET):
    def __init__(self, dataset):
        super(QDialog, self).__init__(iface.mainWindow())
        self.setupUi(self)

        self.labelTitle.setText(dataset["title"])
        self.labelExports.setText(str(dataset["num_downloads"]))
        self.labelViews.setText(str(dataset["num_views"]))
        self.labelDateAdded.setText(
            parser.parse(dataset["first_published_at"]).strftime("%d, %b %Y")
        )
        self.labelLastUpdated.setText(
            parser.parse(dataset["published_at"]).strftime("%d, %b %Y")
        )
        self.labelLayerId.setText(str(dataset["id"]))
        if "geometry_type" == dataset["data"]:
            self.labelDataType.setText(
                f'<b>Data type</b>: {dataset["data"]["geometry_type"]}.'
                ' {dataset["data"]["feature_count"]} features'
            )
        else:
            self.labelDataType.setText("<b>Data type</b>: ---.")
        downloadThumbnail(dataset["thumbnail_url"], self)
        self.labelMap.setFixedSize(360, 189)
        self.txtDescription.setHtml(dataset["description_html"])

    def setThumbnail(self, img):
        thumbnail = QPixmap(img)
        thumb = thumbnail.scaled(360, 189, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.labelMap.setPixmap(thumb)
