from typing import (
    List,
    Optional
)

from qgis.PyQt.QtCore import QProcess
from qgis.core import (
    QgsTask,
    QgsBlockingProcess,
    QgsFeedback,
    QgsReferencedRectangle
)


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
            self._kart_executable = None

        self._arguments = arguments
        self._feedback: Optional[QgsFeedback] = None
        self._errors = []
        self._output = []

    def errors(self) -> List[str]:
        """
        Returns a list of encountered error messages
        """
        return self._errors

    def output(self) -> List[str]:
        """
        Returns the command output
        """
        return self._output

    def run(self):
        if not self._kart_executable:
            return False

        self._feedback = QgsFeedback()

        process = QgsBlockingProcess(self._kart_executable, self._arguments)

        def on_stdout(ba):
            val = ba.data().decode('UTF-8')
            on_stdout.buffer += val

            if on_stdout.buffer.endswith('\n') or on_stdout.buffer.endswith(
                    '\r'):
                # flush buffer
                self._output.append(on_stdout.buffer.rstrip())
                on_stdout.buffer = ''

        on_stdout.buffer = ''

        def on_stderr(ba):
            val = ba.data().decode('UTF-8')
            on_stderr.buffer += val

            if on_stderr.buffer.endswith('\n') or on_stderr.buffer.endswith(
                    '\r'):
                # flush buffer
                self._errors.append(on_stderr.buffer.rstrip())
                on_stderr.buffer = ''

        on_stderr.buffer = ''

        process.setStdOutHandler(on_stdout)
        process.setStdErrHandler(on_stderr)

        res = process.run(self._feedback)

        self._feedback = None

        return process.exitStatus() == QProcess.NormalExit and res == 0

    def cancel(self):
        if self._feedback:
            self._feedback.cancel()

        super().cancel()


class KartCloneTask(KartTask):
    """
    A task for cloning a repo
    """

    def __init__(self,
                 title: str,
                 url: str,
                 destination: str,
                 location: Optional[str] = None,
                 extent: Optional[QgsReferencedRectangle] = None,
                 username: Optional[str] = None,
                 password: Optional[str] = None):
        from kart.kartapi import (
            Repository
        )

        commands = Repository.generate_clone_arguments(
            url,
            destination,
            location=location,
            extent=extent,
            username=username,
            password=password,
        )

        super().__init__(
            self.tr('Cloning {}').format(title),
            commands
        )

        self.destination = destination
        self.repo: Optional[Repository] = None

    def run(self):
        self.repo = None

        res = super().run()
        if res:
            from kart.kartapi import (
                Repository
            )

            self.repo = Repository(self.destination)

        return res
