from qgis.PyQt.QtWidgets import (
    QWidget,
    QGridLayout,
    QVBoxLayout,
    QHBoxLayout,
    QToolButton,
    QSizePolicy
)
from qgis.gui import (
    QgsFilterLineEdit
)

from .access_filter_widget import AccessFilterWidget
from .data_type_filter_widget import DataTypeFilterWidget
from .license_filter_widget import LicenseFilterWidget
from .resolution_filter_widget import ResolutionFilterWidget


class FilterWidget(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Preferred)

        vl = QVBoxLayout()
        vl.setContentsMargins(0, 0, 0, 0)

        hl = QHBoxLayout()
        hl.setContentsMargins(0, 0, 0, 0)

        self.search_line_edit = QgsFilterLineEdit()
        self.search_line_edit.setShowClearButton(True)
        self.search_line_edit.setShowSearchIcon(True)
        hl.addWidget(self.search_line_edit)

        self.show_advanced_button = QToolButton()
        self.show_advanced_button.setText('Advanced')
        self.show_advanced_button.setCheckable(True)
        hl.addWidget(self.show_advanced_button)
        self.show_advanced_button.toggled.connect(self._show_advanced)

        self.clear_all_button = QToolButton()
        self.clear_all_button.setText('Clear All')
        self.clear_all_button.clicked.connect(self._clear_all)
        hl.addWidget(self.clear_all_button)

        vl.addLayout(hl)

        self.advanced_frame = QWidget()
        self.advanced_frame.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Preferred)
        advanced_layout = QGridLayout()

        advanced_layout.setContentsMargins(0, 0, 0, 0)
        self.data_type_filter_widget = DataTypeFilterWidget(self)
        self.resolution_widget = ResolutionFilterWidget(self)
        self.license_widget = LicenseFilterWidget(self)
        self.access_widget = AccessFilterWidget(self)
        advanced_layout.addWidget(self.data_type_filter_widget, 0, 1)
        advanced_layout.addWidget(self.resolution_widget, 1, 0)
        advanced_layout.addWidget(self.license_widget, 2, 0)
        advanced_layout.addWidget(self.access_widget, 2, 1)
        self.advanced_frame.setLayout(advanced_layout)

        vl.addWidget(self.advanced_frame)

        self.advanced_frame.hide()

        self.setLayout(vl)

    def _clear_all(self):
        self.data_type_filter_widget.clear()
        self.resolution_widget.clear()
        self.license_widget.clear()
        self.access_widget.clear()

    def _show_advanced(self, show):
        self.advanced_frame.setVisible(show)
        self.advanced_frame.setMinimumWidth(self.width())
        self.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Preferred)
        self.adjustSize()
