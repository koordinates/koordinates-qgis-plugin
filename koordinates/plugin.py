import os
from typing import Optional

from qgis.PyQt import sip
from qgis.PyQt.QtWidgets import QAction
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtCore import (
    Qt,
    QCoreApplication,
    QEvent
)

from qgis.core import (
    QgsApplication
)

from koordinates.gui.koordinates import Koordinates
from koordinates.gui import KoordinatesDataItemProvider

pluginPath = os.path.dirname(__file__)


def icon(f):
    return QIcon(os.path.join(pluginPath, "img", f))


class KoordinatesPlugin(object):
    def __init__(self, iface):
        self.iface = iface
        self.dock: Optional[Koordinates] = None
        self.explorerAction: Optional[QAction] = None
        self.data_item_provider: Optional[KoordinatesDataItemProvider] = None

    def initGui(self):
        self.dock = Koordinates()
        self.iface.addDockWidget(Qt.RightDockWidgetArea, self.dock)

        self.explorerAction = QAction("Show Data Browser", self.iface.mainWindow())
        self.explorerAction.setCheckable(True)
        self.dock.setToggleVisibilityAction(self.explorerAction)

        self.iface.addPluginToMenu("Koordinates", self.explorerAction)

        self.dock.hide()

        self.data_item_provider = KoordinatesDataItemProvider()
        QgsApplication.dataItemProviderRegistry().addProvider(
            self.data_item_provider
        )

    def unload(self):
        if not sip.isdeleted(self.dock):
            self.dock.cancel_active_requests()
            self.iface.removeDockWidget(self.dock)
            self.dock.deleteLater()
        self.dock = None

        self.iface.removePluginMenu("Koordinates", self.explorerAction)

        if self.data_item_provider and \
                not sip.isdeleted(self.data_item_provider):
            QgsApplication.dataItemProviderRegistry().removeProvider(
                self.data_item_provider
            )
        self.data_item_provider = None

        QCoreApplication.sendPostedEvents(None, QEvent.DeferredDelete)
