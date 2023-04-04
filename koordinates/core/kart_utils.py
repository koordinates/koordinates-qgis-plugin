from typing import (
    Optional,
    List
)

from qgis.PyQt import sip
from qgis.PyQt.QtCore import QEventLoop
from qgis.PyQt.QtWidgets import QWidget


class KartNotInstalledException(Exception):
    """
    Raised when the Kart plugin is not installed
    """


class KartUtils:
    """
    Contains Kart integration support utilities
    """

    CURRENT_CLONE_DIALOG: Optional['CloneDialog'] = None
    CLONE_KART_REPO_WAS_ACCEPTED: bool = False

    @staticmethod
    def clone_kart_repo(title: str,
                        url: str,
                        username: Optional[str],
                        password: Optional[str],
                        parent: Optional[QWidget]):
        """
        Shows a dialog for cloning a kart repository
        """
        import qgis

        if KartUtils.CURRENT_CLONE_DIALOG is not None and \
                not sip.isdeleted(KartUtils.CURRENT_CLONE_DIALOG):
            KartUtils.CURRENT_CLONE_DIALOG.close()
            KartUtils.CURRENT_CLONE_DIALOG.deleteLater()
            KartUtils.CURRENT_CLONE_DIALOG = None

        if "kart" not in qgis.utils.plugins:
            raise KartNotInstalledException()
        kart_plugin = qgis.utils.plugins["kart"]

        try:
            from ..gui.clonedialog import CloneDialog
            from kart.kartapi import Repository, KartException

            KartUtils.CURRENT_CLONE_DIALOG = CloneDialog(parent)
            KartUtils.CURRENT_CLONE_DIALOG.setWindowTitle(
                'Get Data Repository — {}'.format(title))
            KartUtils.CURRENT_CLONE_DIALOG.show()
            KartUtils.CURRENT_CLONE_DIALOG.activateWindow()
            KartUtils.CURRENT_CLONE_DIALOG.raise_()
            el = QEventLoop()

            KartUtils.CLONE_KART_REPO_WAS_ACCEPTED = False

            def on_accept():
                el.quit()
                KartUtils.CLONE_KART_REPO_WAS_ACCEPTED = True

            def on_reject():
                el.quit()

            KartUtils.CURRENT_CLONE_DIALOG.clone.connect(on_accept)
            KartUtils.CURRENT_CLONE_DIALOG.was_canceled.connect(on_reject)
            KartUtils.CURRENT_CLONE_DIALOG.destroyed.connect(on_reject)

            el.exec_()

            if KartUtils.CLONE_KART_REPO_WAS_ACCEPTED:
                extent = KartUtils.CURRENT_CLONE_DIALOG.extent()
                destination = KartUtils.CURRENT_CLONE_DIALOG.destination()
                location = KartUtils.CURRENT_CLONE_DIALOG.location()
                KartUtils.CURRENT_CLONE_DIALOG.deleteLater()
                KartUtils.CURRENT_CLONE_DIALOG = None

                try:
                    repo = Repository.clone(
                        url,
                        destination,
                        location=location,
                        extent=extent,
                        username=username,
                        password=password,
                    )
                    kart_plugin.dock.reposItem.addRepoToUI(repo)
                except KartException:
                    raise KartNotInstalledException()

                return True
            else:
                if KartUtils.CURRENT_CLONE_DIALOG:
                    KartUtils.CURRENT_CLONE_DIALOG.deleteLater()
                KartUtils.CURRENT_CLONE_DIALOG = None
                return False

        except ImportError:
            raise KartNotInstalledException()

    @staticmethod
    def get_kart_repos() -> List['Repository']:
        """
        Returns a list of the cloned kart repositories
        """
        try:
            from kart import kartapi
            return kartapi.repos()[:]

        except ImportError:
            raise KartNotInstalledException()

    @staticmethod
    def get_kart_repo_paths() -> List[str]:
        """
        Returns a list of the cloned kart repository paths
        """
        try:
            from kart import kartapi
            return [repo.path for repo in kartapi.repos()]

        except ImportError:
            raise KartNotInstalledException()
