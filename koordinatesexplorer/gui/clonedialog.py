from typing import Optional

from qgis.PyQt import uic
from qgis.PyQt.QtCore import (
    QDir,
    pyqtSignal
)

from qgis.PyQt.QtWidgets import (
    QDialog,
    QSizePolicy,
    QVBoxLayout,
    QLayout
)
from qgis.core import (
    Qgis,
    QgsReferencedRectangle,
    QgsSettings
)
from qgis.gui import (
    QgsGui,
    QgsMessageBar,
    QgsFileWidget,
)
from qgis.utils import iface

from .gui_utils import GuiUtils
from .locationselectionpanel import LocationSelectionPanel, InvalidLocationException
from .extentselectionpanel import ExtentSelectionPanel

WIDGET, _ = uic.loadUiType(GuiUtils.get_ui_file_path('clonedialog.ui'))


class CloneDialog(QDialog, WIDGET):

    clone = pyqtSignal()
    was_canceled = pyqtSignal()

    def __init__(self, parent=None):
        parent = parent or iface.mainWindow()
        super().__init__(parent)
        self.setupUi(self)

        self.setObjectName('CloneDialog')
        QgsGui.enableAutoGeometryRestore(self)

        self.bar = QgsMessageBar()
        self.bar.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Fixed)
        self.layout().insertWidget(0, self.bar)

        settings = QgsSettings()

        self.dest_widget = QgsFileWidget()
        self.dest_widget.setDialogTitle(self.tr('Select Directory to Clone To'))
        self.dest_widget.setStorageMode(QgsFileWidget.StorageMode.GetDirectory)
        self.dest_widget.lineEdit().setShowClearButton(False)
        self.dest_widget.setDefaultRoot(
            settings.value("koordinates/lastDir", QDir.homePath(), str, QgsSettings.Plugins)
        )

        def store_last_dir():
            QgsSettings().setValue(
                "koordinates/lastDir",
                self.dest_widget.filePath(),
                QgsSettings.Plugins
            )

            self.raise_()
            self.activateWindow()

        self.dest_widget.fileChanged.connect(store_last_dir)

        dest_layout = QVBoxLayout()
        dest_layout.setContentsMargins(0, 0, 0, 0)
        dest_layout.addWidget(self.dest_widget)
        self.folder_widget_frame.setLayout(dest_layout)

        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)

        self.extentPanel = ExtentSelectionPanel(self)
        self.extentPanel.setEnabled(False)

        extent_layout = QVBoxLayout()
        extent_layout.setContentsMargins(0, 0, 0, 0)
        extent_layout.addWidget(self.extentPanel)
        self.extent_widget_frame.setLayout(extent_layout)
        self.extent_widget_frame.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)

        self.check_spatial_filter.toggled.connect(self.extentPanel.setEnabled)

        self.locationPanel = LocationSelectionPanel(show_label=False)

        location_layout = QVBoxLayout()
        location_layout.setContentsMargins(0, 0, 0, 0)
        location_layout.addWidget(self.locationPanel)
        self.location_widget_frame.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        self.location_widget_frame.setLayout(location_layout)

        self.window().layout().setSizeConstraint(QLayout.SetFixedSize)

    def reject(self):
        self.was_canceled.emit()
        super().reject()

    def accept(self):
        try:
            self.locationPanel.location()
        except InvalidLocationException:
            self.bar.pushMessage(
                "Invalid location definition", Qgis.Warning, duration=5
            )
            return

        if self.check_spatial_filter.isChecked():
            extent = self.extent()
            if extent is None:
                self.bar.pushMessage("Invalid extent value", Qgis.Warning, duration=5)
                return

        if not self.destination():
            self.bar.pushMessage(
                "Destination must not be empty", Qgis.Warning, duration=5
            )
        else:
            super().accept()
            self.clone.emit()

    def destination(self) -> str:
        """
        Returns the destination folder
        """
        return self.dest_widget.filePath()

    def location(self):
        """
        Returns the destination location details
        """
        return self.locationPanel.location()

    def extent(self) -> Optional[QgsReferencedRectangle]:
        """
        Returns the output extent
        """
        if self.check_spatial_filter.isChecked():
            return self.extentPanel.getExtent()
        else:
            return None
