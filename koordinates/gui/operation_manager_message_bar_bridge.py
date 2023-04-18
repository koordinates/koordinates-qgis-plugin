from typing import Optional

from qgis.PyQt import sip
from qgis.PyQt.QtCore import (
    QObject
)
from qgis.PyQt.QtWidgets import (
    QPushButton,
    QProgressBar
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
    KartOperationManager,
    KartOperation
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
        self._progress_bar: Optional[QProgressBar] = None

        self._completed_count = 0

        self._manager.task_progress_changed.connect(
            self._report_operation_progress
        )

        self._manager.single_task_canceled.connect(
            self._clear
        )

        self._manager.task_completed.connect(
            self._report_operation_success
        )
        self._manager.single_task_failed.connect(
            self._report_operation_error
        )

    def _clear(self):
        """
        Clears the existing message bar item
        """
        if self._current_item and not sip.isdeleted(self._current_item):
            self._bar.popWidget(self._current_item)
        self._current_item = None
        self._completed_count = 0

    def _create_new_item(self, title: str) -> QgsMessageBarItem:
        """
        Destroys the current message bar item, and creates a new one
        with the given title
        """
        if not self._current_item or sip.isdeleted(self._current_item):
            self._completed_count = 0

        if self._current_item and not sip.isdeleted(self._current_item):
            self._bar.popWidget(self._current_item)

        self._current_item = self._bar.createMessage('', title)
        return self._current_item

    def _report_operation_progress(self,
                                   operation: str,
                                   tasks_in_progress: int,
                                   progress: float):
        """
        Reports operation progress
        """
        if tasks_in_progress == 1:
            if self._completed_count:
                title = self.tr('{} {} dataset. {} completed').format(
                     operation,
                     tasks_in_progress,
                    self._completed_count
                    )
            else:
                title = operation
        elif tasks_in_progress > 1:
            if self._completed_count:
                title = self.tr('{} {} datasets. {} completed').format(
                     operation,
                     tasks_in_progress,
                    self._completed_count
                    )
            else:
                title = self.tr('{} {} datasets.').format(
                     operation,
                     tasks_in_progress
                    )
        else:
            title = operation

        item = self._create_new_item(
            title
        )
        self._progress_bar = QProgressBar()
        self._progress_bar.setRange(0, 100)
        item.layout().addWidget(self._progress_bar)

        cancel_button = QPushButton(self.tr('Cancel'))
        item.layout().addWidget(cancel_button)
        cancel_button.clicked.connect(self._manager.cancel)

        self._progress_bar.setValue(int(progress))

        self._bar.pushWidget(
            item,
            Qgis.MessageLevel.Info,
            0
        )

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

    def _report_operation_success(self,
                                  operation: KartOperation,
                                  message: str,
                                  remaining_tasks: int,
                                  remaining_progress: Optional[float]):
        self._completed_count += 1
        if remaining_tasks == 0:
            if self._completed_count == 1:
                title = message
            else:
                title = self.tr('{} {} datasets.').format(
                    operation.to_present_tense_string(),
                    self._completed_count
                )

            item = self._create_new_item(title)
            self._bar.pushWidget(
                item,
                Qgis.MessageLevel.Success,
                QgsMessageBar.defaultMessageTimeout(Qgis.MessageLevel.Success)
            )
        else:
            if remaining_tasks == 1:
                title = self.tr('{} 1 dataset. {} completed.').format(
                    operation.to_past_tense_string(),
                    self._completed_count
                )
            else:
                title = self.tr('{} {} datasets. {} completed.').format(
                    operation.to_past_tense_string(),
                    remaining_tasks,
                    self._completed_count
                )

            item = self._create_new_item(title)
            self._bar.pushWidget(
                item,
                Qgis.MessageLevel.Info,
                0
            )