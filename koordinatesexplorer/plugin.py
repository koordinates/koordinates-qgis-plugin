import os
from typing import Optional

from qgis.PyQt import sip
from qgis.PyQt.QtWidgets import QAction
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtCore import Qt

from koordinatesexplorer.gui.koordinatesexplorer import KoordinatesExplorer

pluginPath = os.path.dirname(__file__)


def icon(f):
    return QIcon(os.path.join(pluginPath, "img", f))


class KoordinatesPlugin(object):
    def __init__(self, iface):
        self.iface = iface
        self.dock: Optional[KoordinatesExplorer] = None
        self.explorerAction: Optional[QAction] = None

    def initGui(self):
        self.dock = KoordinatesExplorer()
        self.iface.addDockWidget(Qt.RightDockWidgetArea, self.dock)

        self.explorerAction = QAction("Show Data Browser", self.iface.mainWindow())
        self.explorerAction.setCheckable(True)
        self.dock.setToggleVisibilityAction(self.explorerAction)

        self.iface.addPluginToMenu("Koordinates", self.explorerAction)

        self.dock.hide()

    def unload(self):
        if not sip.isdeleted(self.dock):
            self.iface.removeDockWidget(self.dock)
            self.dock.deleteLater()
        self.dock = None

        self.iface.removePluginMenu("Koordinates", self.explorerAction)
