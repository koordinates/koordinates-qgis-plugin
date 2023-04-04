from qgis.PyQt.QtCore import (
    Qt,
    QSize
)
from qgis.PyQt.QtWidgets import (
    QToolButton,
    QSizePolicy
)
from qgis.core import (
    Qgis,
    QgsApplication
)
from qgis.utils import iface

from koordinates.utils import cloneKartRepo, KartNotInstalledException
from .gui_utils import GuiUtils
from ..api import (
    KoordinatesClient,
    UserCapability,
    LayerUtils
)

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

    BUTTON_COLOR = "#0a9b46"
    BUTTON_OUTLINE = "#076d31"
    BUTTON_TEXT = "#ffffff"
    BUTTON_HOVER = "#077936"

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setToolButtonStyle(Qt.ToolButtonIconOnly)
        self.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Maximum)
        self.setStyleSheet(self.BASE_STYLE.format(
            self.BUTTON_COLOR,
            self.BUTTON_OUTLINE,
            self.BUTTON_TEXT,
            self.BUTTON_HOVER))


class CloneButton(ActionButton):
    BUTTON_COLOR = "#f5f5f7"
    BUTTON_OUTLINE = "#c4c4c6"
    BUTTON_TEXT = "#323233"
    BUTTON_HOVER = "#e4e4e6"

    def __init__(self, dataset, parent=None, close_parent_on_clone=False):
        super().__init__(parent)

        self.dataset = dataset

        self.setText("Get")
        icon = GuiUtils.get_icon('clone_button.svg')
        self.setIcon(icon)
        self.setIconSize(QSize(46, 11))
        self.clicked.connect(self.cloneRepository)
        self.setFixedSize(67, self.BUTTON_HEIGHT)

        self._close_parent_on_clone = close_parent_on_clone

    def cloneRepository(self):
        if self._close_parent_on_clone:
            self.parent().close()
        url = self.dataset.get("repository", {}).get("clone_location_https")
        title = self.dataset.get('title')

        from .action_dialog import ActionDialog
        if UserCapability.EnableKartClone not in KoordinatesClient.instance().user_capabilities():
            dlg = ActionDialog(
                title='Get Data Repository — {}'.format(title),
                message='To clone cloud-hosted data to your local drive, please request access.',
                action='Request access',
                url='https://m.koordinates.com/request-kart-features')
            dlg.exec_()
            return

        try:
            if cloneKartRepo(
                    title=title,
                    url=url,
                    username="kart",
                    password=KoordinatesClient.instance().apiKey,
                    parent=iface.mainWindow()
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

    def __init__(self, dataset, parent=None):
        super().__init__(parent)

        self.dataset = dataset

        self.setText("+Add")

        icon = GuiUtils.get_icon('add_button.svg')
        self.setIcon(icon)
        self.setIconSize(QSize(53, 11))
        self.clicked.connect(self.add_layer)
        self.setFixedSize(72, self.BUTTON_HEIGHT)

    def add_layer(self):
        """
        Adds the layer to the current project
        """
        LayerUtils.add_layer_to_project(self.dataset)
