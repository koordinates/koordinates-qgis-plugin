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

    # emitted when an error occurs, with title and error message
    error_occurred = pyqtSignal(str, str)

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

            def call_onfail_and_pop(_task: KartTask):
                """
                Ensure that the on_fail callback is always called
                before cleaning up the task
                """
                on_fail(_task)
                self._pop_task(_task)

            task.taskTerminated.connect(partial(call_onfail_and_pop, task))
        else:
            task.taskTerminated.connect(partial(self._pop_task, task))

        QgsApplication.taskManager().addTask(task)

    def _pop_task(self, task: KartTask):
        """
        Removes a finished task from the manager
        """
        self._ongoing_tasks = [t for t in self._ongoing_tasks if t != task]

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
            repo = _task.repo

            # if kart plugin is not available then a KartNotInstalledException
            # will have been raised when creating the KartCloneTask
            from kart.core import RepoManager
            RepoManager.instance().add_repo(repo)

        def on_task_terminated(_task: KartTask):
            self.error_occurred.emit(
                self.tr('Failed to clone ...'),
                '\n'.join(_task.output())
            )

        self._push_task(task,
                        on_complete=on_task_complete,
                        on_fail=on_task_terminated)
