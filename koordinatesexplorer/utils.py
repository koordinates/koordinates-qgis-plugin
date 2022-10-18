from qgis.PyQt import sip
from qgis.PyQt.QtCore import Qt, QEventLoop
from qgis.PyQt.QtWidgets import QApplication


def waitcursor(method):
    def func(*args, **kw):
        try:
            QApplication.setOverrideCursor(Qt.WaitCursor)
            return method(*args, **kw)
        except Exception as ex:
            raise ex
        finally:
            QApplication.restoreOverrideCursor()

    return func


class KartNotInstalledException(Exception):
    pass


CURRENT_CLONE_DIALOG = None


def cloneKartRepo(title: str, url, username, password, parent):
    import qgis
    global CURRENT_CLONE_DIALOG

    if CURRENT_CLONE_DIALOG is not None and not sip.isdeleted(CURRENT_CLONE_DIALOG):
        CURRENT_CLONE_DIALOG.close()
        CURRENT_CLONE_DIALOG.deleteLater()
        CURRENT_CLONE_DIALOG = None

    if "kart" not in qgis.utils.plugins:
        raise KartNotInstalledException()
    kart_plugin = qgis.utils.plugins["kart"]

    try:
        from .gui.clonedialog import CloneDialog
        from kart.kartapi import Repository, KartException

        CURRENT_CLONE_DIALOG = CloneDialog(parent)
        CURRENT_CLONE_DIALOG.setWindowTitle('Clone — {}'.format(title))
        CURRENT_CLONE_DIALOG.show()
        CURRENT_CLONE_DIALOG.activateWindow()
        CURRENT_CLONE_DIALOG.raise_()
        el = QEventLoop()

        cloneKartRepo.was_accepted = False

        def on_accept():
            el.quit()
            cloneKartRepo.was_accepted = True

        def on_reject():
            el.quit()

        CURRENT_CLONE_DIALOG.clone.connect(on_accept)
        CURRENT_CLONE_DIALOG.was_canceled.connect(on_reject)

        el.exec_()

        if cloneKartRepo.was_accepted:
            extent = CURRENT_CLONE_DIALOG.extent()
            destination = CURRENT_CLONE_DIALOG.destination()
            location = CURRENT_CLONE_DIALOG.location()
            CURRENT_CLONE_DIALOG.deleteLater()
            CURRENT_CLONE_DIALOG = None

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
            if CURRENT_CLONE_DIALOG:
                CURRENT_CLONE_DIALOG.deleteLater()
            CURRENT_CLONE_DIALOG = None
            return False

    except ImportError:
        raise KartNotInstalledException()
