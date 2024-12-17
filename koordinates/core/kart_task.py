import re
from typing import (
    List,
    Optional,
    Tuple
)

from qgis.PyQt.QtCore import QProcess
from qgis.core import (
    QgsTask,
    QgsBlockingProcess,
    QgsFeedback,
    QgsReferencedRectangle
)

from .enums import KartOperation
from .exceptions import KartNotInstalledException


class KartTask(QgsTask):
    """
    A task for running kart commands in a background thread
    """

    def __init__(self, description: str, arguments: List[str]):
        super().__init__(description)

        try:
            from kart.kartapi import (
                kartExecutable
            )
            self._kart_executable = kartExecutable()
        except ImportError:
            raise KartNotInstalledException

        if not self._kart_executable:
            raise KartNotInstalledException

        self._arguments = arguments
        self._feedback: Optional[QgsFeedback] = None
        self._output = []
        self._result: bool = False
        self._was_canceled: bool = False

        self._stdout_buffer = ''

    def operation(self) -> KartOperation:
        """
        Returns the associated kart operation
        """
        return KartOperation.Unknown

    def short_result_description(self) -> str:
        """
        Returns a short description of the task's result
        """
        return self.tr('Success')

    def was_canceled(self) -> bool:
        """
        Returns True if the task was canceled
        """
        return self._was_canceled

    def result(self) -> Tuple[bool, str, str]:
        """
        Returns the task's result, as a tuple of:

        - True for success
        - Short description of result
        - Detailed description of result
        """
        return (
            self._result,
            self.short_result_description(),
            '<br>'.join(self._output)
        )

    def output(self) -> List[str]:
        """
        Returns the command output
        """
        return self._output

    def on_stdout(self, ba):
        """
        Called when the kart process emits messages on stdout
        """
        val = ba.data().decode('UTF-8', errors='replace')
        self._stdout_buffer += val

        if self._stdout_buffer.endswith('\n') or self._stdout_buffer.endswith(
                '\r'):
            # flush buffer
            self._output.append(self._stdout_buffer.rstrip())
            self._stdout_buffer = ''

    def run(self):
        self._feedback = QgsFeedback()

        self.setProgress(1)

        process = QgsBlockingProcess(self._kart_executable, self._arguments)

        def on_stdout(ba):
            self.on_stdout(ba)

        # kart executable throws all sorts of non-error output to stderr,
        # so consider stdout and stderr as equivalent
        process.setStdOutHandler(on_stdout)
        process.setStdErrHandler(on_stdout)

        res = process.run(self._feedback)

        self._feedback = None

        self._result = bool(process.exitStatus() == QProcess.NormalExit
                            and res == 0)
        return self._was_canceled or self._result

    def cancel(self):
        if self._feedback:
            self._feedback.cancel()
            self._was_canceled = True

        super().cancel()


class KartCloneTask(KartTask):
    """
    A task for cloning a repo
    """

    # let's say counting takes.... 5% of time.
    COUNT_PERCENT_OF_TIME = 0.05

    def __init__(self,
                 title: str,
                 url: str,
                 destination: str,
                 location: Optional[str] = None,
                 extent: Optional[QgsReferencedRectangle] = None,
                 username: Optional[str] = None,
                 password: Optional[str] = None):
        try:
            from kart.kartapi import (
                Repository
            )
        except ImportError:
            raise KartNotInstalledException()

        commands = Repository.generate_clone_arguments(
            url,
            destination,
            location=location,
            extent=extent,
            username=username,
            password=password,
        )

        super().__init__(
            'Cloning {}'.format(title),
            commands
        )

        self.title = title
        self.url = url
        self.destination = destination
        self.location = location
        self.extent = extent
        self.username = username
        self.password = password
        self.repo: Optional[Repository] = None

    def operation(self):
        return KartOperation.Clone

    def short_result_description(self) -> str:
        return (
            self.tr('Cloned {}') if self._result
            else self.tr('Failed to clone {}')
        ).format(self.title)

    def on_stdout(self, ba):
        val = ba.data().decode('UTF-8', errors='replace')

        counting_regex = re.compile(r'.*Counting objects:?\s*(\d+)%.*')
        receiving_regex = re.compile(r'.*Receiving objects:?\s*(\d+)%.*')

        counting_match = counting_regex.search(val)
        percent = None

        if counting_match:
            percent = int(counting_match.group(1)) * \
                      KartCloneTask.COUNT_PERCENT_OF_TIME
        else:
            receiving_match = receiving_regex.search(val)
            if receiving_match:
                percent = int(receiving_match.group(1)) * \
                          (1 - KartCloneTask.COUNT_PERCENT_OF_TIME) \
                          + KartCloneTask.COUNT_PERCENT_OF_TIME

        if percent is not None:
            self.setProgress(percent)

        super().on_stdout(ba)

    def run(self):
        self.repo = None

        res = super().run()
        if res:
            from kart.kartapi import (
                Repository
            )

            self.repo = Repository(self.destination)

        return res
