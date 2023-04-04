from typing import Optional

from qgis.PyQt import sip
from qgis.PyQt.QtCore import (
    Qt,
    QCoreApplication,
    QEvent
)
from qgis.PyQt.QtWidgets import (
    QAction,
    QPushButton
)

from qgis.core import (
    Qgis,
    QgsApplication,
    QgsMessageOutput
)


from koordinates.gui.koordinates import Koordinates
from .core import KartOperationManager
from .gui import KoordinatesDataItemProvider


class KoordinatesPlugin(object):
    def __init__(self, iface):
        self.iface = iface
        self.dock: Optional[Koordinates] = None
        self.explorerAction: Optional[QAction] = None
        self.data_item_provider: Optional[KoordinatesDataItemProvider] = None
        self._kart_operation_manager: Optional[KartOperationManager] = None

    def initGui(self):
        self._kart_operation_manager = KartOperationManager()
        KartOperationManager._instance = self._kart_operation_manager

        self._kart_operation_manager.error_occurred.connect(
            self._report_operation_error
        )

        self.dock = Koordinates()
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

        if self._kart_operation_manager and \
                not sip.isdeleted(self._kart_operation_manager):
            self._kart_operation_manager.deleteLater()
        self._kart_operation_manager = None
        KartOperationManager._instance = None

        QCoreApplication.sendPostedEvents(None, QEvent.DeferredDelete)

    def _report_operation_error(self, title: str, error: str):
        def show_details(_):
            dialog = QgsMessageOutput.createMessageOutput()
            dialog.setTitle(title)
            dialog.setMessage(error, QgsMessageOutput.MessageHtml)
            dialog.showMessage()

        message_widget = self.iface.messageBar().createMessage('',
                                                               title)
        details_button = QPushButton("View Details")
        details_button.clicked.connect(show_details)
        message_widget.layout().addWidget(details_button)
        self.iface.messageBar().pushWidget(message_widget,
                                           Qgis.MessageLevel.Critical,
                                           0)
