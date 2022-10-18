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


def cloneKartRepo(title: str, url, username, password, parent):
    import qgis

    if "kart" not in qgis.utils.plugins:
        raise KartNotInstalledException()
    kart_plugin = qgis.utils.plugins["kart"]

    try:
        from .gui.clonedialog import CloneDialog
        from kart.kartapi import Repository

        dialog = CloneDialog(parent)
        dialog.setWindowTitle('Clone — {}'.format(title))
        dialog.show()
        el = QEventLoop()

        cloneKartRepo.was_accepted = False

        def on_accept():
            el.quit()
            cloneKartRepo.was_accepted = True

        def on_reject():
            el.quit()

        dialog.clone.connect(on_accept)
        dialog.was_canceled.connect(on_reject)

        el.exec_()

        if cloneKartRepo.was_accepted:
            extent = dialog.extent()
            destination = dialog.destination()
            location = dialog.location()
            dialog.deleteLater()
            del dialog

            repo = Repository.clone(
                url,
                destination,
                location=location,
                extent=extent,
                username=username,
                password=password,
            )
            kart_plugin.dock.reposItem.addRepoToUI(repo)
            return True
        else:
            dialog.deleteLater()
            return False

    except ImportError:
        raise KartNotInstalledException()
