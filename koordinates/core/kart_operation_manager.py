from functools import partial
from typing import (
    Optional,
    Callable,
    List
)

from qgis.PyQt.QtCore import (
    Qt,
    QAbstractItemModel,
    QModelIndex,
    pyqtSignal
)
from qgis.core import (
    QgsApplication,
    QgsReferencedRectangle,
    QgsTask
)

from .enums import (
    KartOperation,
    OperationStatus
)
from .kart_task import (
    KartCloneTask,
    KartTask
)


class FailedOperationDetails:
    """
    Encapsulates information about a failed operation
    """

    def __init__(self,
                 description: str,
                 error: str):
        self.description = description
        self.error = error


class KartOperationManager(QAbstractItemModel):
    """
    Keeps track of ongoing kart operations.

    Implemented as a model.
    """

    DescriptionRole = Qt.UserRole + 1
    ProgressRole = Qt.UserRole + 2
    DetailsRole = Qt.UserRole + 3
    StatusRole = Qt.UserRole + 4

    # operation, description, remaining tasks, overall remaining progress
    task_completed = pyqtSignal(KartOperation, str, int, float)

    # operation, description, error message, remaining tasks, overall remaining progress
    task_failed = pyqtSignal(KartOperation, str, str, int, float)

    single_task_canceled = pyqtSignal()

    # operation, description, count ongoing tasks, overall progress
    task_progress_changed = pyqtSignal(KartOperation, str, int, float)

    # emitted when a clone operation starts.
    # argument is clone URL
    clone_started = pyqtSignal(str)

    # emitted regardless of whether the clone was successful or not
    # argument is clone URL
    clone_finished = pyqtSignal(str)

    _instance: Optional['KartOperationManager'] = None

    @classmethod
    def instance(cls) -> 'KartOperationManager':
        """
        Returns the operation manager instance
        """
        return KartOperationManager._instance

    def __init__(self):
        super().__init__()

        self._ongoing_tasks: List[QgsTask] = []
        self._failures: List[FailedOperationDetails] = []

    def clear_errors(self):
        """
        Clears all error results from the manager
        """
        if not self._failures:
            return

        self.beginRemoveRows(QModelIndex(), len(self._ongoing_tasks),
                             self.rowCount())
        self._failures = []
        self.endRemoveRows()

    def _push_task(self,
                   task: KartTask,
                   on_complete: Optional[Callable[[KartTask], None]] = None,
                   on_fail: Optional[Callable[[KartTask], None]] = None,
                   on_cancel: Optional[Callable[[KartTask], None]] = None):
        """
        Pushes a new active task to the manager
        """
        self.beginInsertRows(QModelIndex(), len(self._ongoing_tasks),
                             len(self._ongoing_tasks))
        self._ongoing_tasks.append(task)
        self.endInsertRows()

        if on_complete is not None or on_cancel is not None:

            def call_on_complete_and_pop(_task: KartTask):
                """
                Ensure that the on_complete callback is always called
                before cleaning up the task
                """
                if not _task.was_canceled():
                    if on_complete is not None:
                        on_complete(_task)
                else:
                    if on_cancel is not None:
                        on_cancel(_task)

                self._pop_task(_task)

            task.taskCompleted.connect(partial(call_on_complete_and_pop, task))
        else:
            task.taskCompleted.connect(partial(self._pop_task, task))

        if on_fail is not None:

            def call_on_fail_and_pop(_task: KartTask):
                """
                Ensure that the on_fail callback is always called
                before cleaning up the task
                """
                on_fail(_task)
                self._task_failed(_task)

            task.taskTerminated.connect(partial(call_on_fail_and_pop, task))
        else:
            task.taskTerminated.connect(partial(self._task_failed, task))

        task.progressChanged.connect(self._emit_progress_message)
        task.statusChanged.connect(self._task_status_changed)

        QgsApplication.taskManager().addTask(task)

    def _task_failed(self, task: KartTask):
        """
        Called when a task has failed
        """
        result, short_description, detailed_description = task.result()
        details = FailedOperationDetails(description=short_description,
                                         error=detailed_description)

        self._pop_task(task)

        self.beginInsertRows(QModelIndex(), self.rowCount(), self.rowCount())
        self._failures.append(details)
        self.endInsertRows()

    def _pop_task(self, task: KartTask):
        """
        Removes a finished task from the manager
        """
        result, short_description, detailed_description = task.result()
        was_canceled = task.was_canceled()

        task_index = self._ongoing_tasks.index(task)
        self.beginRemoveRows(QModelIndex(), task_index, task_index)
        del self._ongoing_tasks[task_index]
        self.endRemoveRows()

        remaining_progress = self.calculate_remaining_progress()

        if was_canceled:
            if len(self._ongoing_tasks) == 0:
                self.single_task_canceled.emit()
            else:
                self._emit_progress_message()
        else:
            if result:
                self.task_completed.emit(task.operation(),
                                         short_description,
                                         len(self._ongoing_tasks),
                                         remaining_progress)
            else:
                self.task_failed.emit(task.operation(),
                                      short_description,
                                      detailed_description,
                                      len(self._ongoing_tasks),
                                      remaining_progress)

    def calculate_remaining_progress(self) -> float:
        """
        Returns the overall progress of remaining tasks
        """
        if not self._ongoing_tasks:
            return -1

        return 100 * sum(t.progress() for t in self._ongoing_tasks) / \
            (100 * len(self._ongoing_tasks))

    def _emit_progress_message(self):
        """
        Emits progress report signals
        """
        if len(self._ongoing_tasks) == 1:
            self.task_progress_changed.emit(
                self._ongoing_tasks[0].operation(),
                self._ongoing_tasks[0].description(),
                1,
                self._ongoing_tasks[0].progress()
            )
        elif all(isinstance(t, KartCloneTask) for t in self._ongoing_tasks):
            self.task_progress_changed.emit(
                KartOperation.Clone,
                '',
                len(self._ongoing_tasks),
                self.calculate_remaining_progress()
            )
        else:
            # mixed task types, not handled yet
            assert False

        task = self.sender()
        if task:
            try:
                task_index = self._ongoing_tasks.index(task)
                index = self.index(task_index, 0, QModelIndex())
                self.dataChanged.emit(index, index)
            except ValueError:
                pass

    def _task_status_changed(self):
        """
        Called when a task's status is changed
        """
        task = self.sender()
        if task:
            task_index = self._ongoing_tasks.index(task)
            index = self.index(task_index, 0, QModelIndex())
            self.dataChanged.emit(index, index)

    def cancel(self):
        """
        Cancels all ongoing tasks
        """
        for t in self._ongoing_tasks:
            t.cancel()

    def start_clone(self,
                    title: str,
                    url: str,
                    destination: str,
                    location: Optional[str] = None,
                    extent: Optional[QgsReferencedRectangle] = None,
                    username: Optional[str] = None,
                    password: Optional[str] = None):
        """
        Starts a clone operation in a background thread

        :raises: KartNotInstalledException if kart plugin is not installed
        """
        task = KartCloneTask(
            title,
            url,
            destination,
            location=location,
            extent=extent,
            username=username,
            password=password,
        )

        def on_task_complete(_task: KartCloneTask):
            # if kart plugin is not available then a KartNotInstalledException
            # will have been raised when creating the KartCloneTask
            from kart.core import RepoManager  # NOQA
            RepoManager.instance().add_repo(_task.repo)
            self.clone_finished.emit(_task.url)

        def on_task_failed_or_cancel(_task: KartCloneTask):
            self.clone_finished.emit(_task.url)

        self._push_task(task,
                        on_complete=on_task_complete,
                        on_fail=on_task_failed_or_cancel,
                        on_cancel=on_task_failed_or_cancel
                        )

        self.clone_started.emit(url)

    def is_cloning(self, url: str) -> bool:
        """
        Returns True if the dataset is currently being cloned
        """
        for task in self._ongoing_tasks:
            if isinstance(task, KartCloneTask):
                if task.url == url and task.status() not in (
                        QgsTask.Complete, QgsTask.Terminated):
                    return True

        return False

    # Qt model interface

    # pylint: disable=missing-docstring, unused-arguments
    def index(self, row, column, parent=QModelIndex()):
        if column < 0 or column >= self.columnCount():
            return QModelIndex()

        if not parent.isValid() and 0 <= (row < len(
                self._ongoing_tasks) + len(self._failures)):
            return self.createIndex(row, column)

        return QModelIndex()

    def parent(self, index):
        return QModelIndex()  # all are top level items

    def rowCount(self, parent=QModelIndex()):
        if not parent.isValid():
            return len(self._ongoing_tasks) + len(self._failures)
        # no child items
        return 0

    def columnCount(self, parent=QModelIndex()):
        return 1

    def data(self, index, role=Qt.DisplayRole):
        task = self.index2task(index)
        if task:
            if role == self.DescriptionRole:
                return task.description()
            if role == self.ProgressRole:
                return task.progress()
            if role == self.StatusRole:
                return OperationStatus.Ongoing
        failed_task = self.index2failed_task_details(index)
        if failed_task:
            if role == self.DescriptionRole:
                return failed_task.description
            if role == self.DetailsRole:
                return failed_task.error
            if role == self.StatusRole:
                return OperationStatus.Failed

        return None

    def flags(self, index):
        f = super().flags(index)
        if not index.isValid():
            return f

        return f | Qt.ItemIsEnabled

    # pylint: enable=missing-docstring, unused-arguments

    def cancel_task(self, index: QModelIndex):
        """
        Cancels the task at the specified model index
        """

        task = self.index2task(index)
        if task:
            task.cancel()

    def index2task(self, index: QModelIndex) -> Optional[QgsTask]:
        """
        Returns the task at the given model index
        """
        if not index.isValid() or index.row() < 0 or index.row() >= len(
                self._ongoing_tasks):
            return None

        return self._ongoing_tasks[index.row()]

    def index2failed_task_details(self, index: QModelIndex) -> \
            Optional[FailedOperationDetails]:
        """
        Returns the details of the failed operation at the given model index
        """
        if not index.isValid() or index.row() < len(self._ongoing_tasks) or \
                index.row() >= len(self._ongoing_tasks) + len(self._failures):
            return None

        return self._failures[index.row() - len(self._ongoing_tasks)]
