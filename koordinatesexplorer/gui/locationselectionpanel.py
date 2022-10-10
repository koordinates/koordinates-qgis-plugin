import os

from qgis.PyQt import uic
from qgis.PyQt.QtWidgets import (
    QWidget,
    QLabel
)

WIDGET, BASE = uic.loadUiType(
    os.path.join(os.path.dirname(__file__), "locationselectionpanel.ui")
)


class InvalidLocationException(Exception):
    pass


class LocationSelectionPanel(QWidget, WIDGET):
    def __init__(self, show_label=True):
        super().__init__()

        self.setupUi(self)

        if show_label:
            self.type_label = QLabel('Storage type')
            self.type_layout.insertWidget(0, self.type_label)
        else:
            self.type_label = None

        self.comboChanged(0)
        self.comboStorageType.currentIndexChanged.connect(self.comboChanged)

    def comboChanged(self, idx):
        self.grpPostgis.setVisible(idx != 0)
        self.updateGeometry()
        self.adjustSize()

    def location(self):
        if self.comboStorageType.currentIndex() == 0:
            return None
        else:
            host = self.txtHost.text().strip()
            port = self.txtPort.text().strip()
            database = self.txtDatabase.text().strip()
            schema = self.txtSchema.text().strip()
            if "" in [host, port, database, schema]:
                raise InvalidLocationException
            return f"postgresql://{host}:{port}/{database}/{schema}"
