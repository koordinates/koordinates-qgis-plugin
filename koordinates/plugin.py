from typing import Optional

from qgis.PyQt import sip
from qgis.PyQt.QtCore import (
    Qt,
    QCoreApplication,
    QEvent
)
from qgis.PyQt.QtWidgets import (
    QAction
)

from qgis.core import (
    QgsApplication
)


from koordinates.gui.koordinates import Koordinates
from .core import KartOperationManager
from .gui import (
    KoordinatesDataItemProvider,
    OperationManagerMessageBarBridge
)


class KoordinatesPlugin:
    """
    Main plugin interface
    """

    def __init__(self, iface):
        self.iface = iface
        self.dock: Optional[Koordinates] = None
        self.explorerAction: Optional[QAction] = None
        self.data_item_provider: Optional[KoordinatesDataItemProvider] = None
        self._kart_operation_manager: Optional[KartOperationManager] = None
        self._operation_manager_bridge: \
            Optional[OperationManagerMessageBarBridge] = None

    def initGui(self):
        self._kart_operation_manager = KartOperationManager()
        KartOperationManager._instance = self._kart_operation_manager

        self._operation_manager_bridge = OperationManagerMessageBarBridge(
                self._kart_operation_manager,
                self.iface.messageBar()
        )

        self.dock = Koordinates(self.iface.mainWindow())
        self.iface.addDockWidget(Qt.RightDockWidgetArea, self.dock)

        self.explorerAction = QAction("Show Data Browser",
                                      self.iface.mainWindow())
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

        if self._operation_manager_bridge and \
                not sip.isdeleted(self._operation_manager_bridge):
            self._operation_manager_bridge.deleteLater()
        self._operation_manager_bridge = None

        if self._kart_operation_manager and \
                not sip.isdeleted(self._kart_operation_manager):
            self._kart_operation_manager.deleteLater()
        self._kart_operation_manager = None
        KartOperationManager._instance = None

        QCoreApplication.sendPostedEvents(None, QEvent.DeferredDelete)
