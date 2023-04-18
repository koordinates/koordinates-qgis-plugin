from functools import partial
from typing import (
    Optional,
    Callable
)

from qgis.PyQt.QtCore import (
    QObject,
    pyqtSignal
)
from qgis.core import (
    QgsApplication,
    QgsReferencedRectangle
)

from .enums import KartOperation
from .kart_task import (
    KartCloneTask,
    KartTask
)


class KartOperationManager(QObject):
    """
    Keeps track of ongoing kart operations
    """

    # operation, description, remaining tasks, overall remaining progress
    task_completed = pyqtSignal(KartOperation, str, int, float)

    # operation, description, error message, remaining tasks, overall remaining progress
    task_failed = pyqtSignal(KartOperation, str, str, int, float)

    single_task_canceled = pyqtSignal()

    # operation, description, count ongoing tasks, overall progress
    task_progress_changed = pyqtSignal(KartOperation, str, int, float)

    _instance: Optional['KartOperationManager'] = None

    @classmethod
    def instance(cls) -> 'KartOperationManager':
        """
        Returns the operation manager instance
        """
        return KartOperationManager._instance

    def __init__(self):
        super().__init__()

        self._ongoing_tasks = []

    def _push_task(self,
                   task: KartTask,
                   on_complete: Optional[Callable[[KartTask], None]] = None,
                   on_fail: Optional[Callable[[KartTask], None]] = None):
        """
        Pushes a new active task to the manager
        """
        self._ongoing_tasks.append(task)

        if on_complete is not None:

            def call_on_complete_and_pop(_task: KartTask):
                """
                Ensure that the on_complete callback is always called
                before cleaning up the task
                """
                if not _task.was_canceled():
                    on_complete(_task)
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
                self._pop_task(_task)

            task.taskTerminated.connect(partial(call_on_fail_and_pop, task))
        else:
            task.taskTerminated.connect(partial(self._pop_task, task))

        task.progressChanged.connect(self._emit_progress_message)

        QgsApplication.taskManager().addTask(task)

    def _pop_task(self, task: KartTask):
        """
        Removes a finished task from the manager
        """
        result, short_description, detailed_description = task.result()
        was_canceled = task.was_canceled()

        self._ongoing_tasks = [t for t in self._ongoing_tasks if t != task]

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

        def on_task_complete(_task: KartTask):
            # if kart plugin is not available then a KartNotInstalledException
            # will have been raised when creating the KartCloneTask
            from kart.core import RepoManager  # NOQA
            RepoManager.instance().add_repo(_task.repo)

        self._push_task(task,
                        on_complete=on_task_complete)
