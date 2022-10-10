import os
from typing import Optional

from qgis.PyQt import uic
from qgis.PyQt.QtWidgets import (
    QWidget,
)
from qgis.core import (
    QgsRectangle,
    QgsReferencedRectangle,
)
from qgis.gui import (
    QgsMapToolExtent
)
from qgis.utils import iface

WIDGET, BASE = uic.loadUiType(
    os.path.join(os.path.dirname(__file__), "extentselectionpanel.ui")
)


class ExtentSelectionPanel(QWidget, WIDGET):
    """
    Custom widget for easy selection of a map extent
    """

    MODE_CANVAS = 'MODE_CANVAS'
    MODE_SELECT = 'MODE_SELECT'
    MODE_LAYER = 'MODE_LAYER'

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setupUi(self)

        self.combo_mode.addItem(self.tr('Use Visible Map Extent'),
                                ExtentSelectionPanel.MODE_CANVAS)
        self.combo_mode.addItem(self.tr('Select Extent On Map'), ExtentSelectionPanel.MODE_SELECT)
        self.combo_mode.addItem(self.tr('Use Layer Extent'), ExtentSelectionPanel.MODE_LAYER)
        self.combo_mode.currentIndexChanged.connect(self._mode_changed)

        self.button_select_from_map.clicked.connect(self.draw_on_canvas)

        self.prev_map_tool = None
        self.tool = None
        self._custom_extent: Optional[QgsReferencedRectangle] = None

        self._mode_changed()

    def _mode_changed(self):
        """
        Triggered when the mode is changed
        """
        if self.combo_mode.currentData() == ExtentSelectionPanel.MODE_CANVAS:
            self.stacked_widget.setCurrentWidget(self.page_canvas)
        elif self.combo_mode.currentData() == ExtentSelectionPanel.MODE_SELECT:
            self.stacked_widget.setCurrentWidget(self.page_select)
        elif self.combo_mode.currentData() == ExtentSelectionPanel.MODE_LAYER:
            self.stacked_widget.setCurrentWidget(self.page_layer)

    def draw_on_canvas(self):
        self.prev_map_tool = iface.mapCanvas().mapTool()
        if not self.tool:
            self.tool = QgsMapToolExtent(iface.mapCanvas())
            self.tool.extentChanged.connect(self.extent_drawn)
            self.tool.deactivated.connect(self.map_tool_deactivated)
        iface.mapCanvas().setMapTool(self.tool)

        self.toggle_dialog_visibility(False)

    def extent_drawn(self, rect: QgsRectangle):
        self._custom_extent = QgsReferencedRectangle(
            rect,
            iface.mapCanvas().mapSettings().destinationCrs()
        )
        iface.mapCanvas().setMapTool(self.prev_map_tool)
        self.toggle_dialog_visibility(True)
        self.prev_map_tool = None

    def map_tool_deactivated(self):
        self.toggle_dialog_visibility(True)
        self.prev_map_tool = None

    def toggle_dialog_visibility(self, visible: bool):
        dialog = self.window()
        if dialog.objectName() == 'QgisApp':
            return

        if not visible:
            dialog.setVisible(False)
        else:
            dialog.setVisible(True)
            dialog.raise_()
            dialog.activateWindow()

    def canvas_extent(self) -> QgsReferencedRectangle:
        return QgsReferencedRectangle(
            iface.mapCanvas().extent(),
            iface.mapCanvas().mapSettings().destinationCrs(),
        )

    def getExtent(self) -> QgsReferencedRectangle:
        if self.combo_mode.currentData() == ExtentSelectionPanel.MODE_CANVAS:
            return self.canvas_extent()
        elif self.combo_mode.currentData() == ExtentSelectionPanel.MODE_SELECT:
            return self._custom_extent
        elif self.combo_mode.currentData() == ExtentSelectionPanel.MODE_LAYER:
            return QgsReferencedRectangle(self.layer_combo.currentLayer().extent(),
                                          self.layer_combo.currentLayer().crs())
