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
    QgsMessageBar
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

        self._manager.single_task_completed.connect(
            self._report_operation_success
        )
        self._manager.single_task_failed.connect(
            self._report_operation_error
        )

    def _report_operation_error(self, title: str, error: str):
        def show_details(_):
            dialog = QgsMessageOutput.createMessageOutput()
            dialog.setTitle(title)
            dialog.setMessage(error, QgsMessageOutput.MessageHtml)
            dialog.showMessage()

        message_widget = self.iface.messageBar().createMessage('',
                                                               title)
        details_button = QPushButton("View Details")
        details_button.clicked.connect(show_details)
        message_widget.layout().addWidget(details_button)
        self._bar.pushWidget(message_widget,
                             Qgis.MessageLevel.Critical,
                             0)

    def _report_operation_success(self, title: str):
        message_widget = self.iface.messageBar().createMessage('',
                                                               title)
        self._bar.pushWidget(message_widget,
                             Qgis.MessageLevel.Success,
                             0)
