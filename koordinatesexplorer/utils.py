from qgis.PyQt.QtCore import Qt
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

def cloneKartRepo(url, parent):
    try:
        from kart.gui.clonedialog import CloneDialog
        from kart.kartapi import Repository
        dialog = CloneDialog(parent)
        dialog.txtSrc.setText(url)
        dialog.show()
        ret = dialog.exec_()
        if ret == dialog.Accepted:
            Repository.clone(
                dialog.src, dialog.dst, dialog.location, dialog.extent
            )
            return True
        else:
            return False
    except ImportError:
        raise KartNotInstalledException()

