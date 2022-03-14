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

        self.dataset = dataset

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
        if "geometry_type" in dataset["data"]:
            self.labelDataType.setText(
                f'<b>Data type</b>: {dataset["data"]["geometry_type"]}.'
                f' {dataset["data"]["feature_count"]} features'
            )
        else:
            self.labelDataType.setText("<b>Data type</b>: ---.")
        downloadThumbnail(dataset["thumbnail_url"], self)
        self.labelMap.setFixedSize(360, 189)
        self.txtDescription.setHtml(self._html())

    def _html(self):
        if self.dataset["data"].get("fields") is not None:
            extra = f"""
                </tr><tr>
                <td>Data type</td> <td>{self.dataset["data"]["geometry_type"]}</td>
                </tr><tr>
                <td> Feature count </td><td> {self.dataset["data"]["feature_count"]} </td>
                </tr><tr>
                  <td> Attributes </td><td>{", ".join([f["name"] for f in self.dataset["data"]["fields"]])}</td>
            """

        elif "feature_count" in self.dataset["data"]:
            extra = f"""
                </tr><tr>
                <td> Tile count </td><td> {self.dataset["data"]["feature_count"]} </td>
            """
        else:
            extra = ""
        html = f"""
            <p>{self.dataset["description_html"]}</p>
            <h3>Koordinates categories</h3>
            {"<br>".join([cat["name"] for cat in self.dataset["categories"]])}
            <h3>Tags</h3>
            {" | ".join(self.dataset["tags"])}
            <h3>Details</h3>
            <p>
            <table>
              <tbody>
                <tr>
                  <td> Layer ID </td><td> {self.dataset["id"]}</td>
                  {extra}
                </tr><tr>
                  <td> Stored CRS </td><td>{self.dataset["data"]["crs_display"]}</td>
                </tr>
              </tbody>
            </table>
            </p>
        """
        return html

    def setThumbnail(self, img):
        thumbnail = QPixmap(img)
        thumb = thumbnail.scaled(360, 189, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.labelMap.setPixmap(thumb)
