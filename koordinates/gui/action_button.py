from qgis.PyQt.QtCore import (
    Qt,
    QSize
)
from qgis.PyQt.QtGui import (
    QPainter,
    QColor,
    QPen
)
from qgis.PyQt.QtWidgets import (
    QToolButton,
    QSizePolicy
)
from qgis.core import (
    Qgis
)
from qgis.utils import iface

from .gui_utils import GuiUtils
from ..api import (
    KoordinatesClient,
    LayerUtils,
    Dataset,
    UserDatasetCapability
)
from ..core import (
    KartOperationManager
)
from ..core import (
    KartUtils,
    KartNotInstalledException
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

    def __init__(self, dataset: Dataset, parent=None,
                 close_parent_on_clone=False):
        super().__init__(parent)

        self.dataset = dataset
        self.clicked.connect(self.cloneRepository)

        self._close_parent_on_clone = close_parent_on_clone

        KartOperationManager.instance().clone_started.connect(
            self._update_state,
            Qt.QueuedConnection
        )
        KartOperationManager.instance().clone_finished.connect(
            self._update_state,
            Qt.QueuedConnection
        )

        self._update_state()

    def _update_state(self):
        """
        Updates button state based on current operations
        """
        is_cloning = \
            self.dataset.repository() and \
            KartOperationManager.instance().is_cloning(
                self.dataset.repository().clone_url()
            )

        self.setEnabled(not is_cloning)
        if is_cloning:
            icon = GuiUtils.get_icon('cloning_button.svg')
            self.setIcon(icon)
            self.setIconSize(QSize(65, 17))
            self.setFixedSize(99, self.BUTTON_HEIGHT)

            self.setText(self.tr('Cloning'))
        else:
            icon = GuiUtils.get_icon('clone_button.svg')
            self.setIcon(icon)
            self.setIconSize(QSize(60, 11))
            self.setFixedSize(77, self.BUTTON_HEIGHT)

            self.setText(self.tr('Clone'))

    def cloneRepository(self):
        if not self.dataset.repository():
            return

        if self._close_parent_on_clone:
            self.parent().close()
        url = self.dataset.repository().clone_url()
        title = self.dataset.title()

        from .action_dialog import ActionDialog

        if UserDatasetCapability.Clone not in \
                self.dataset.repository().user_capabilities():

            message_text = """
<h1>Cloning of published data is in private beta</h1>
<p>We're still working on the user experience of cloning published data from
authoritative publishers.</p>
<p>You can request access to the private beta below.</p>
            """
            dlg = ActionDialog(
                title='Get Data Repository — {}'.format(title),
                message=message_text,
                action='Request Kart beta access',
                url='https://m.koordinates.com/request-kart-features')
            dlg.exec_()
            return

        try:
            KartUtils.clone_kart_repo(
                title=title,
                url=url,
                username="kart",
                password=KoordinatesClient.instance().apiKey,
                parent=iface.mainWindow()
            )
        except KartNotInstalledException:
            iface.messageBar().pushMessage(
                "Kart plugin must be installed to clone repositories",
                Qgis.Warning,
                duration=5,
            )


class AddButton(ActionButton):

    def __init__(self, dataset: Dataset, parent=None):
        super().__init__(parent)

        self.dataset = dataset

        self.styles = self.dataset.styles()

        self.setText("+Add")
        self._show_divider = False
        if len(self.styles) > 1:
            icon = GuiUtils.get_icon('add_button_with_menu.svg')
            self._show_divider = True
        else:
            icon = GuiUtils.get_icon('add_button.svg')
        self.setIcon(icon)
        self.setIconSize(QSize(53, 11))
        self.clicked.connect(self.add_layer)
        self.setFixedSize(72, self.BUTTON_HEIGHT)

    def paintEvent(self, event):
        super().paintEvent(event)
        if self._show_divider:
            painter = QPainter(self)

            pen = QPen()
            pen.setWidth(1)
            pen.setColor(QColor(self.BUTTON_OUTLINE))

            painter.setPen(pen)
            painter.setBrush(Qt.NoBrush)

            divider_x = int(self.width() * 0.65)
            painter.drawLine(divider_x, 1,
                             divider_x, self.height()-1)

            painter.end()

    def add_layer(self):
        """
        Adds the layer to the current project
        """
        LayerUtils.add_layer_to_project(self.dataset)
