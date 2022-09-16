from qgis.PyQt.QtCore import QTimer
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
from .gui_utils import GuiUtils
from ..api import DataBrowserQuery

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
        self.show_advanced_button.setIcon(GuiUtils.get_icon('filter.svg'))
        self.show_advanced_button.setText('Advanced')
        self.show_advanced_button.setToolTip('Advanced')
        self.show_advanced_button.setCheckable(True)
        hl.addWidget(self.show_advanced_button)
        self.show_advanced_button.toggled.connect(self._show_advanced)

        self.clear_all_button = QToolButton()
        self.clear_all_button.setText('Clear All')
        self.clear_all_button.clicked.connect(self._clear_all)
        # a QToolButton with an icon will appear smaller by default vs one with text, so
        # force the advanced button to match the Clear All button size
        self.show_advanced_button.setFixedHeight(self.clear_all_button.sizeHint().height())
        self.show_advanced_button.setFixedWidth(self.show_advanced_button.height())
        hl.addWidget(self.clear_all_button)

        vl.addLayout(hl)

        # these are dynamically created
        self.advanced_frame = None
        self.advanced_layout = None

        self.data_type_filter_widget = DataTypeFilterWidget(self)
        self.resolution_widget = ResolutionFilterWidget(self)
        self.license_widget = LicenseFilterWidget(self)
        self.access_widget = AccessFilterWidget(self)

        self.filter_widgets = (self.data_type_filter_widget,
                               self.resolution_widget,
                               self.license_widget,
                               self.access_widget)

        # changes to filter parameters are deferred to a small timeout, to avoid
        # starting lots of queries while a user is mid-operation (such as dragging a slider)
        self._update_query_timeout = QTimer(self)
        self._update_query_timeout.setSingleShot(True)
        self._update_query_timeout.timeout.connect(self._update_query)

        for w in self.filter_widgets:
            w.changed.connect(self._filter_widget_changed)
        self.search_line_edit.textChanged.connect(self._filter_widget_changed)

        self.visible_widgets = self.filter_widgets[:]

        self.setLayout(vl)

        self._reflow()

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

    def _reflow(self):
        """
        Rearranges the filter widgets based on what's visible
        """
        item_index = 0

        for widget in self.filter_widgets:
            widget.setParent(None)

        self.advanced_layout = QGridLayout()
        self.advanced_layout.setContentsMargins(0, 0, 0, 0)


        row = 0
        column = 0
        for widget in self.visible_widgets:
            self.advanced_layout.addWidget(widget, row, column)
            column += 1
            if column > 1:
                row += 1
                column = 0

        self.advanced_frame = QWidget()
        self.advanced_frame.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Preferred)

        self.advanced_frame.setLayout(self.advanced_layout)

        self.advanced_frame.setVisible(self.show_advanced_button.isChecked())


        self.layout().addWidget(self.advanced_frame)

        self.advanced_frame.adjustSize()

    def _filter_widget_changed(self):
        # changes to filter parameters are deferred to a small timeout, to avoid
        # starting lots of queries while a user is mid-operation (such as dragging a slider)
        self._update_query_timeout.start(500)

    def _update_query(self):
        query = DataBrowserQuery()

        if self.search_line_edit.text().strip():
            query.search = self.search_line_edit.text().strip()

        for w in self.filter_widgets:
            w.apply_constraints_to_query(query)

        print(query.build_query())

