from qgis.PyQt.QtCore import QTimer
from qgis.PyQt.QtWidgets import (
    QWidget,
    QGridLayout,
    QVBoxLayout,
    QHBoxLayout,
    QToolButton,
    QSizePolicy,
    QStackedWidget,
    QSpacerItem
)
from qgis.gui import (
    QgsFilterLineEdit
)

from .access_filter_widget import AccessFilterWidget
from .data_type_filter_widget import DataTypeFilterWidget
from .license_filter_widget import LicenseFilterWidget
from .resolution_filter_widget import ResolutionFilterWidget
from .date_filter_widget import DateFilterWidget
from .gui_utils import GuiUtils
from ..api import (
    DataBrowserQuery,
    DataType
)


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

        # Warning: we can't create a dynamic QLayout for these widgets, as it is NOT possible
        # to re-parent a QgsFloatingWidget without risk of crashing.
        # Accordingly, we instead use a stacked widget with two different layouts (one for grid/raster and
        # one for all other types), and have multiple filter widgets shown on the different stacked widget pages
        self.data_type_filter_widget_1 = DataTypeFilterWidget(self)
        self.data_type_filter_widget_2 = DataTypeFilterWidget(self)
        self.resolution_widget = ResolutionFilterWidget(self)
        self.date_filter_widget_1 = DateFilterWidget(self)
        self.date_filter_widget_2 = DateFilterWidget(self)
        self.license_widget_1 = LicenseFilterWidget(self)
        self.license_widget_2 = LicenseFilterWidget(self)
        self.access_widget_1 = AccessFilterWidget(self)
        self.access_widget_2 = AccessFilterWidget(self)

        self.advanced_stacked_widget = QStackedWidget()
        self.advanced_stacked_widget.setVisible(False)
        self.advanced_stacked_widget.setSizePolicy(self.advanced_stacked_widget.sizePolicy().horizontalPolicy(), QSizePolicy.Maximum)

        self.filter_widget_page_non_grid = QWidget()
        filter_widget_layout_1 = QGridLayout()
        filter_widget_layout_1.setContentsMargins(0,0,0,0)
        filter_widget_layout_1.addWidget(self.data_type_filter_widget_1, 0, 1)
        filter_widget_layout_1.addWidget(self.date_filter_widget_1, 1, 0)
        filter_widget_layout_1.addWidget(self.license_widget_1, 1, 1)
        filter_widget_layout_1.addWidget(self.access_widget_1, 2, 0)
        #filter_widget_layout_1.addItem(QSpacerItem(1,1, QSizePolicy.Ignored, QSizePolicy.Expanding), 2,0)
        self.filter_widget_page_non_grid.setLayout(filter_widget_layout_1)
        self.advanced_stacked_widget.addWidget(self.filter_widget_page_non_grid)

        self.filter_widget_page_grid = QWidget()
        filter_widget_layout_2 = QGridLayout()
        filter_widget_layout_2.setContentsMargins(0,0,0,0)
        filter_widget_layout_2.addWidget(self.data_type_filter_widget_2, 0, 1)
        filter_widget_layout_2.addWidget(self.resolution_widget, 1, 0)
        filter_widget_layout_2.addWidget(self.date_filter_widget_2, 1, 1)
        filter_widget_layout_2.addWidget(self.license_widget_2, 2, 0)
        filter_widget_layout_2.addWidget(self.access_widget_2, 2, 1)
        self.filter_widget_page_grid.setLayout(filter_widget_layout_2)
        self.advanced_stacked_widget.addWidget(self.filter_widget_page_grid)
        self.advanced_stacked_widget.setCurrentWidget(self.filter_widget_page_grid)

        self.filter_widgets = (self.data_type_filter_widget_1,
                               self.data_type_filter_widget_2,
                               self.resolution_widget,
                               self.date_filter_widget_1,
                               self.date_filter_widget_2,
                               self.license_widget_1,
                               self.license_widget_2,
                                self.access_widget_1,
                               self.access_widget_2)

        # changes to filter parameters are deferred to a small timeout, to avoid
        # starting lots of queries while a user is mid-operation (such as dragging a slider)
        self._update_query_timeout = QTimer(self)
        self._update_query_timeout.setSingleShot(True)
        self._update_query_timeout.timeout.connect(self._update_query)

        for w in self.filter_widgets:
            w.changed.connect(self._filter_widget_changed)
        self.search_line_edit.textChanged.connect(self._filter_widget_changed)

        vl.addWidget(self.advanced_stacked_widget)

        self.setLayout(vl)

    def _current_filter_widgets(self):
        if self.advanced_stacked_widget.currentWidget() == self.filter_widget_page_non_grid:
            return (self.data_type_filter_widget_1,
                    self.license_widget_1,
                    self.date_filter_widget_1,
                    self.access_widget_1)
        else:
            return (self.data_type_filter_widget_2,
                    self.resolution_widget,
                    self.date_filter_widget_2,
                    self.license_widget_2,
                    self.access_widget_2)

    def _clear_all(self):
        for w in self.filter_widgets:
            w.clear()
        self.search_line_edit.clear()

    def _show_advanced(self, show):
        if not show:
            for w in self.filter_widgets:
                w.collapse()
        self.advanced_stacked_widget.setVisible(show)
        self.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Preferred)
        self.advanced_stacked_widget.adjustSize()
        self.adjustSize()

    def data_type_filter_widget(self):
        if self.advanced_stacked_widget.currentWidget() == self.filter_widget_page_non_grid:
            return self.data_type_filter_widget_1
        else:
            return self.data_type_filter_widget_2

    def _filter_widget_changed(self):
        # changes to filter parameters are deferred to a small timeout, to avoid
        # starting lots of queries while a user is mid-operation (such as dragging a slider)
        self._update_query_timeout.start(500)

        selected_data_types = self.data_type_filter_widget().data_types()

        if DataType.Rasters in selected_data_types or DataType.Grids in selected_data_types:
            if self.advanced_stacked_widget.currentWidget() != self.filter_widget_page_grid:
                current_query = self._update_query()
                self.advanced_stacked_widget.setCurrentWidget(self.filter_widget_page_grid)
                for w in (self.data_type_filter_widget_2,
                    self.resolution_widget,
                    self.date_filter_widget_2,
                    self.license_widget_2,
                    self.access_widget_2):
                    w.set_from_query(current_query)
                if self.sender() == self.data_type_filter_widget_1 and self.data_type_filter_widget_1.is_expanded():
                    self.data_type_filter_widget_2.expand()
                for w in (self.data_type_filter_widget_1,
                    self.date_filter_widget_1,
                    self.license_widget_1,
                    self.access_widget_1):
                    w.collapse()
        else:
            if self.advanced_stacked_widget.currentWidget() != self.filter_widget_page_non_grid:
                current_query = self._update_query()
                self.advanced_stacked_widget.setCurrentWidget(self.filter_widget_page_non_grid)
                for w in (self.data_type_filter_widget_1,
                    self.license_widget_1,
                    self.date_filter_widget_1,
                    self.access_widget_1):
                    w.set_from_query(current_query)
                if self.sender() == self.data_type_filter_widget_2 and self.data_type_filter_widget_2.is_expanded():
                    self.data_type_filter_widget_1.expand()
                for w in (self.data_type_filter_widget_2,
                          self.resolution_widget,
                          self.date_filter_widget_2,
                          self.license_widget_2,
                          self.access_widget_2):
                    w.collapse()

    def _update_query(self):
        query = DataBrowserQuery()

        if self.search_line_edit.text().strip():
            query.search = self.search_line_edit.text().strip()

        for w in self._current_filter_widgets():
            w.apply_constraints_to_query(query)

        print(query.build_query())
        return query

