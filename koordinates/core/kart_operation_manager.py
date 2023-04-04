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

from .kart_task import (
    KartCloneTask,
    KartTask
)


class KartOperationManager(QObject):
    """
    Keeps track of ongoing kart operations
    """

    single_task_progress_changed = pyqtSignal(str, float)
    single_task_completed = pyqtSignal(str)
    single_task_failed = pyqtSignal(str, str)

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

        task.progressChanged.connect(
            partial(self._task_progress_changed, task)
        )

        QgsApplication.taskManager().addTask(task)

    def _pop_task(self, task: KartTask):
        """
        Removes a finished task from the manager
        """
        result, short_description, detailed_description = task.result()

        if result:
            if len(self._ongoing_tasks) == 1:
                self.single_task_completed.emit(short_description)
            else:
                assert False
        else:
            if len(self._ongoing_tasks) == 1:
                self.single_task_failed.emit(short_description,
                                             detailed_description)
            else:
                assert False

        self._ongoing_tasks = [t for t in self._ongoing_tasks if t != task]

    def _task_progress_changed(self, task: KartTask, progress: float):
        """
        Called when a task's progress is changed
        """
        if len(self._ongoing_tasks) == 1:
            self.single_task_progress_changed.emit(
                task.description(),
                progress
            )
        else:
            assert False

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
