import os

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

    def initGui(self):
        self.dock = KoordinatesExplorer()
        self.iface.addDockWidget(Qt.RightDockWidgetArea, self.dock)

        self.explorerAction = QAction("Data Browser...", self.iface.mainWindow())
        self.iface.addPluginToMenu("Koordinates", self.explorerAction)
        self.explorerAction.triggered.connect(self.showDock)

        self.dock.hide()

    def showDock(self):
        self.dock.show()

    def unload(self):
        if not sip.isdeleted(self.dock):
            self.iface.removeDockWidget(self.dock)
            self.dock.deleteLater()
        self.dock = None

        self.iface.removePluginMenu("Koordinates", self.explorerAction)
