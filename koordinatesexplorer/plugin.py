import os

from qgis.PyQt.QtWidgets import QAction
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtCore import Qt

from koordinatesexplorer.gui.koordinatesexplorer import KoordinatesExplorer
from koordinatesexplorer.gui.testexplorer import TestExplorer

pluginPath = os.path.dirname(__file__)


def icon(f):
    return QIcon(os.path.join(pluginPath, "img", f))


class KoordinatesPlugin(object):
    def __init__(self, iface):
        self.iface = iface

    def initGui(self):
        self.dock = KoordinatesExplorer()
        self.iface.addDockWidget(Qt.RightDockWidgetArea, self.dock)

        self.explorerAction = QAction(
            "Koordinates explorer...", self.iface.mainWindow()
        )
        self.iface.addPluginToMenu("Koordinates", self.explorerAction)
        self.explorerAction.triggered.connect(self.showDock)

        self.testAction = QAction("Test web view...", self.iface.mainWindow())
        self.testAction.triggered.connect(self.showTestWebView)
        self.iface.addPluginToMenu("Koordinates", self.testAction)

        self.dock.hide()

    def showTestWebView(self):
        dialog = TestExplorer()
        dialog.exec()

    def showDock(self):
        self.dock.show()

    def unload(self):
        self.iface.removeDockWidget(self.dock)
        self.dock = None
        self.iface.removePluginMenu("Koordinates", self.explorerAction)
        self.iface.removePluginMenu("Koordinates", self.testAction)
