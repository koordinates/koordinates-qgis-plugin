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
        self._cancel_button: Optional[QPushButton] = None

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

    def _item_destroyed(self):
        """
        Called when the message bar item is destroyed
        """
        self._completed_count = 0
        self._current_item = None

    def _set_item_state(self,
                        title: str,
                        level: Qgis.MessageLevel,
                        progress: Optional[float] = None,
                        show_cancel_button: bool = False) -> QgsMessageBarItem:
        """
        Ensures that there is a current message bar item, and that it matches
        the specified information level and title
        """
        if not self._current_item or sip.isdeleted(self._current_item):
            self._completed_count = 0

        if self._current_item and not sip.isdeleted(self._current_item):
            if self._current_item.level() != level:
                self._current_item.setLevel(level)
            self._current_item.setDuration(0)
            self._current_item.setText(title)
        else:
            self._current_item = self._bar.createMessage('', title)
            self._current_item.destroyed.connect(self._item_destroyed)
            self._current_item.setLevel(level)
            self._current_item.setDuration(0)
            self._bar.pushItem(
                self._current_item
            )

        if progress is None:
            if self._progress_bar and not sip.isdeleted(self._progress_bar):
                self._progress_bar.deleteLater()
            self._progress_bar = None
        else:
            if not self._progress_bar or sip.isdeleted(self._progress_bar):
                self._progress_bar = QProgressBar()
                self._progress_bar.setRange(0, 100)
                self._current_item.layout().addWidget(self._progress_bar)
            self._progress_bar.setValue(int(progress))

        if not show_cancel_button:
            if self._cancel_button and not sip.isdeleted(self._cancel_button):
                self._cancel_button.deleteLater()
            self._cancel_button = None
        else:
            if not self._cancel_button or sip.isdeleted(self._cancel_button):
                self._cancel_button = QPushButton(self.tr('Cancel'))
                self._current_item.layout().addWidget(self._cancel_button)
                self._cancel_button.clicked.connect(self._manager.cancel)

        return self._current_item

    def _report_operation_progress(self,
                                   operation: KartOperation,
                                   message: str,
                                   tasks_in_progress: int,
                                   progress: float):
        """
        Reports operation progress
        """
        if tasks_in_progress == 1:
            if self._completed_count:
                title = self.tr('{} {} dataset. {} completed').format(
                     operation.to_present_tense_string(),
                     tasks_in_progress,
                     self._completed_count
                    )
            else:
                title = message
        elif tasks_in_progress > 1:
            if self._completed_count:
                title = self.tr('{} {} datasets. {} completed').format(
                     operation.to_present_tense_string(),
                     tasks_in_progress,
                    self._completed_count
                    )
            else:
                title = self.tr('{} {} datasets.').format(
                     operation.to_present_tense_string(),
                     tasks_in_progress
                    )
        else:
            title = message

        self._set_item_state(
            title,
            Qgis.MessageLevel.Info,
            progress,
            show_cancel_button=True
        )

    def _report_operation_error(self, title: str, error: str):
        def show_details(_):
            dialog = QgsMessageOutput.createMessageOutput()
            dialog.setTitle(title)
            dialog.setMessage(error, QgsMessageOutput.MessageHtml)
            dialog.showMessage()

        item = self._set_item_state(title, Qgis.MessageLevel.Critical)
        details_button = QPushButton(self.tr("View Details"))
        details_button.clicked.connect(show_details)
        item.layout().addWidget(details_button)

    def _report_operation_success(self,
                                  operation: KartOperation,
                                  message: str,
                                  remaining_tasks: int,
                                  remaining_progress: float):
        if remaining_progress < 0:
            remaining_progress = None

        self._completed_count += 1
        if remaining_tasks == 0:
            if self._completed_count == 1:
                title = message
            else:
                title = self.tr('{} {} datasets.').format(
                    operation.to_past_tense_string(),
                    self._completed_count
                )

            self._set_item_state(title,
                                 Qgis.MessageLevel.Success,
                                 show_cancel_button=False)
        else:
            if remaining_tasks == 1:
                title = self.tr('{} 1 dataset. {} completed.').format(
                    operation.to_present_tense_string(),
                    self._completed_count
                )
            else:
                title = self.tr('{} {} datasets. {} completed.').format(
                    operation.to_present_tense_string(),
                    remaining_tasks,
                    self._completed_count
                )

            self._set_item_state(title,
                                 Qgis.MessageLevel.Info,
                                 remaining_progress,
                                 show_cancel_button=True)
