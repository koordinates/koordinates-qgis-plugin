from qgis.PyQt.QtCore import (
    Qt,
    QSize
)
from qgis.PyQt.QtWidgets import (
    QToolButton,
    QSizePolicy
)
from qgis.core import Qgis
from qgis.utils import iface

from koordinatesexplorer.utils import cloneKartRepo, KartNotInstalledException
from .gui_utils import GuiUtils
from ..api import KoordinatesClient

COLOR_INDEX = 0


class ActionButton(QToolButton):
    BUTTON_HEIGHT = 32

    BASE_STYLE = """
            QToolButton{{
            background-color: {};
            border-style: solid;
            border-width: 1px;
            border-radius: 4px;
            border-color: {};
            font: bold 14px;
            color: {};
            padding: 2px 0px 2px 0px;
            }}
            QToolButton:hover{{
                background-color: {};
            }}
            """

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setToolButtonStyle(Qt.ToolButtonIconOnly)
        self.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Maximum)


class CloneButton(ActionButton):
    BUTTON_COLOR_CLONE = "#f5f5f7"
    BUTTON_OUTLINE_CLONE = "#c4c4c6"
    BUTTON_TEXT_CLONE = "#323233"
    BUTTON_HOVER_CLONE = "#e4e4e6"

    def __init__(self, dataset, parent=None):
        super().__init__(parent)

        self.dataset = dataset

        self.setText("Clone")
        icon = GuiUtils.get_icon('clone_button.svg')
        self.setIcon(icon)
        self.setIconSize(QSize(63, 11))
        self.setStyleSheet(self.BASE_STYLE.format(
            self.BUTTON_COLOR_CLONE,
            self.BUTTON_OUTLINE_CLONE,
            self.BUTTON_TEXT_CLONE,
            self.BUTTON_HOVER_CLONE))
        self.clicked.connect(self.cloneRepository)
        self.setFixedSize(88, self.BUTTON_HEIGHT)

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


class AddButton(ActionButton):
    BUTTON_COLOR_ADD = "#0a9b46"
    BUTTON_OUTLINE_ADD = "#076d31"
    BUTTON_TEXT_ADD = "#ffffff"
    BUTTON_HOVER_ADD = "#077936"

    def __init__(self, dataset, parent=None):
        super().__init__(parent)

        self.dataset = dataset

        self.setText("+Add")

        icon = GuiUtils.get_icon('add_button.svg')
        self.setIcon(icon)
        self.setIconSize(QSize(53, 11))
        self.setStyleSheet(self.BASE_STYLE.format(self.BUTTON_COLOR_ADD,
                                                  self.BUTTON_OUTLINE_ADD,
                                                  self.BUTTON_TEXT_ADD,
                                                  self.BUTTON_HOVER_ADD))
        self.clicked.connect(self.addLayer)
        self.setFixedSize(72, self.BUTTON_HEIGHT)

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
