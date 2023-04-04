from typing import Optional

from qgis.PyQt import sip
from qgis.PyQt.QtCore import (
    QObject
)
from qgis.PyQt.QtWidgets import (
    QPushButton
)
from qgis.core import (
    Qgis,
    QgsMessageOutput
)
from qgis.gui import (
    QgsMessageBar,
    QgsMessageBarItem
)

from ..core import (
    KartOperationManager
)


class OperationManagerMessageBarBridge(QObject):
    """
    Bridges a Kart operations manager to the QGIS message bar
    """

    def __init__(
            self,
            operations_manager: KartOperationManager,
            message_bar: QgsMessageBar
    ):
        super().__init__()

        self._manager = operations_manager
        self._bar = message_bar

        self._current_item: Optional[QgsMessageBarItem] = None

        self._manager.single_task_completed.connect(
            self._report_operation_success
        )
        self._manager.single_task_failed.connect(
            self._report_operation_error
        )

    def _create_new_item(self, title: str) -> QgsMessageBarItem:
        """
        Destroys the current message bar item, and creates a new one
        with the given title
        """
        if self._current_item and not sip.isdeleted(self._current_item):
            self._bar.popWidget(self._current_item)

        self._current_item = self._bar.createMessage('', title)
        return self._current_item

    def _report_operation_error(self, title: str, error: str):
        def show_details(_):
            dialog = QgsMessageOutput.createMessageOutput()
            dialog.setTitle(title)
            dialog.setMessage(error, QgsMessageOutput.MessageHtml)
            dialog.showMessage()

        item = self._create_new_item(title)
        details_button = QPushButton(self.tr("View Details"))
        details_button.clicked.connect(show_details)
        item.layout().addWidget(details_button)
        self._bar.pushWidget(
            item,
            Qgis.MessageLevel.Critical,
            0
        )

    def _report_operation_success(self, title: str):
        item = self._create_new_item(title)
        self._bar.pushWidget(
            item,
            Qgis.MessageLevel.Success,
            0
        )
