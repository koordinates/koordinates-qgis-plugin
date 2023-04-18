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
        self._failed_count = 0

        self._manager.task_progress_changed.connect(
            self._report_operation_progress
        )

        self._manager.single_task_canceled.connect(
            self._clear
        )

        self._manager.task_completed.connect(
            self._report_operation_success
        )
        self._manager.task_failed.connect(
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
        self._failed_count = 0

    def _item_destroyed(self):
        """
        Called when the message bar item is destroyed
        """
        self._completed_count = 0
        self._failed_count = 0
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
            self._failed_count = 0

        if self._current_item and not sip.isdeleted(self._current_item):
            if self._current_item.level() != level:
                # this sometimes fails to correctly update the message bar
                # appearance...
                self._current_item.setLevel(level)
            self._bar.setStyleSheet(self._current_item.getStyleSheet())

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
        self._update_message(
            operation,
            message,
            tasks_in_progress,
            progress
        )

    def _report_operation_error(self,
                                operation: KartOperation,
                                message: str,
                                error: str,
                                remaining_tasks: int,
                                remaining_progress: float):
        if remaining_progress < 0:
            remaining_progress = None

        def show_details(_):
            dialog = QgsMessageOutput.createMessageOutput()
            dialog.setTitle(message)
            dialog.setMessage(error, QgsMessageOutput.MessageHtml)
            dialog.showMessage()

        self._failed_count += 1

        self._update_message(
            operation,
            message,
            remaining_tasks,
            remaining_progress
        )

       # item = self._set_item_state(title, Qgis.MessageLevel.Critical)
      #  details_button = QPushButton(self.tr("View Details"))
      #  details_button.clicked.connect(show_details)
      #  item.layout().addWidget(details_button)

    def _report_operation_success(self,
                                  operation: KartOperation,
                                  message: str,
                                  remaining_tasks: int,
                                  remaining_progress: float):
        if remaining_progress < 0:
            remaining_progress = None

        self._completed_count += 1
        self._update_message(
            operation,
            message,
            remaining_tasks,
            remaining_progress
        )

    def _update_message(self,
                        operation: KartOperation,
                        message: str,
                        remaining_tasks: int,
                        remaining_progress: float):

        if remaining_tasks == 0:
            # all tasks complete
            if self._failed_count == 1 and self._completed_count == 0:
                title = message
                level = Qgis.MessageLevel.Critical
            elif self._failed_count == 0 and self._completed_count == 1:
                title = message
                level = Qgis.MessageLevel.Success
            elif self._failed_count == 0:
                title = self.tr('{} {} datasets.').format(
                    operation.to_past_tense_string(),
                    self._completed_count
                )
                level = Qgis.MessageLevel.Success
            elif self._completed_count == 0:
                title = self.tr('Failed to {} {} datasets.').format(
                    operation.to_verb(),
                    self._failed_count
                )
                level = Qgis.MessageLevel.Critical
            else:
                # mixed results
                if self._completed_count == 1:
                    title = self.tr('{} 1 dataset. {} failed.').format(
                        operation.to_past_tense_string(),
                        self._failed_count
                    )
                else:
                    title = self.tr('{} {} datasets. {} failed.').format(
                        operation.to_present_tense_string(),
                        self._completed_count,
                        self._failed_count
                    )

                level = Qgis.MessageLevel.Warning

            self._set_item_state(title,
                                 level,
                                 show_cancel_button=False)
        else:
            if self._failed_count == 0 and self._completed_count == 0:
                if remaining_tasks == 1:
                    title = message
                else:
                    title = self.tr('{} {} datasets.').format(
                        operation.to_present_tense_string(),
                        remaining_tasks
                    )
                level = Qgis.MessageLevel.Info
            elif self._failed_count == 0:
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
                level = Qgis.MessageLevel.Info
            elif self._completed_count == 0:
                if remaining_tasks == 1:
                    title = self.tr('{} 1 dataset. {} failed.').format(
                        operation.to_present_tense_string(),
                        self._failed_count
                    )
                else:
                    title = self.tr('{} {} datasets. {} failed.').format(
                        operation.to_present_tense_string(),
                        remaining_tasks,
                        self._failed_count
                    )
                level = Qgis.MessageLevel.Warning
            else:
                if remaining_tasks == 1:
                    title = self.tr(
                        '{} 1 dataset. {} failed. {} completed.').format(
                        operation.to_present_tense_string(),
                        self._failed_count,
                        self._completed_count
                    )
                else:
                    title = self.tr(
                        '{} {} datasets. {} failed. {} completed.').format(
                        operation.to_present_tense_string(),
                        remaining_tasks,
                        self._failed_count,
                        self._completed_count
                    )
                level = Qgis.MessageLevel.Warning

            self._set_item_state(title,
                                 level,
                                 remaining_progress,
                                 show_cancel_button=True)
