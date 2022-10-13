from qgis.PyQt.QtCore import (
    QTimer,
    pyqtSignal
)
from qgis.PyQt.QtWidgets import (
    QWidget,
    QGridLayout,
    QVBoxLayout,
    QHBoxLayout,
    QToolButton,
    QSizePolicy,
    QStackedWidget,
    QSpacerItem,
    QLabel
)
from qgis.PyQt.QtGui import (
    QFontMetrics
)
from qgis.gui import (
    QgsFilterLineEdit
)

from .access_filter_widget import AccessFilterWidget
#  from .category_filter_widget import CategoryFilterWidget
from .data_type_filter_widget import DataTypeFilterWidget
from .date_filter_widget import DateFilterWidget
from .gui_utils import GuiUtils
from .license_filter_widget import LicenseFilterWidget
from .resolution_filter_widget import ResolutionFilterWidget
from ..api import (
    DataBrowserQuery,
    DataType,
    SortOrder
)
from .flow_layout import FlowLayout

class FilterWidget(QWidget):
    filters_changed = pyqtSignal()
    clear_all = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)

        self._starred = False

        self.sort_order = SortOrder.Popularity

        self.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Preferred)

        vl = QVBoxLayout()
        vl.setContentsMargins(0, 0, 0, 0)

        hl = QHBoxLayout()
        hl.setContentsMargins(0, 0, 0, 0)

        self.search_line_edit = QgsFilterLineEdit()
        self.search_line_edit.setShowClearButton(True)
        self.search_line_edit.setShowSearchIcon(True)
        self.search_line_edit.setPlaceholderText('Search')
        self.search_line_edit.setFixedHeight(int(self.search_line_edit.sizeHint().height() * 1.2))
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
        label = QLabel()
        default_font = label.font()
        self.clear_all_button.setFont(default_font)

        # a QToolButton with an icon will appear smaller by default vs one with text, so
        # force the advanced button to match the Clear All button size
        self.show_advanced_button.setFixedHeight(self.clear_all_button.sizeHint().height())
        self.show_advanced_button.setFixedWidth(self.show_advanced_button.height())
        hl.addWidget(self.clear_all_button)

        vl.addLayout(hl)

        # self.category_filter_widget = CategoryFilterWidget(self)
        self.data_type_filter_widget = DataTypeFilterWidget(self)
        self.resolution_widget = ResolutionFilterWidget(self)
        self.date_filter_widget = DateFilterWidget(self)
        self.license_widget = LicenseFilterWidget(self)
        self.access_widget = AccessFilterWidget(self)

        min_filter_widget_width = QFontMetrics(self.font()).width('x')*20
        # self.category_filter_widget.setMinimumWidth(min_filter_widget_width)
        self.data_type_filter_widget.setMinimumWidth(min_filter_widget_width)
        self.resolution_widget.setMinimumWidth(min_filter_widget_width)
        self.date_filter_widget.setMinimumWidth(min_filter_widget_width)
        self.license_widget.setMinimumWidth(min_filter_widget_width)
        self.access_widget.setMinimumWidth(min_filter_widget_width)

        self.filter_widget_page = QWidget()
        filter_widget_layout = FlowLayout()
        filter_widget_layout.setContentsMargins(0, 0, 0, 0)
        # filter_widget_layout.addWidget(self.category_filter_widget)
        filter_widget_layout.addWidget(self.data_type_filter_widget)
        filter_widget_layout.addWidget(self.resolution_widget)
        filter_widget_layout.addWidget(self.date_filter_widget)
        filter_widget_layout.addWidget(self.license_widget)
        filter_widget_layout.addWidget(self.access_widget)
        self.filter_widget_page.setLayout(filter_widget_layout)

        self.filter_widgets = (  # self.category_filter_widget,
            self.data_type_filter_widget,
            self.resolution_widget,
            self.date_filter_widget,
            self.license_widget,
            self.access_widget,)

        # changes to filter parameters are deferred to a small timeout, to avoid
        # starting lots of queries while a user is mid-operation (such as dragging a slider)
        self._update_query_timeout = QTimer(self)
        self._update_query_timeout.setSingleShot(True)
        self._update_query_timeout.timeout.connect(self._update_query)

        for w in self.filter_widgets:
            w.changed.connect(self._filter_widget_changed)
        self.search_line_edit.textChanged.connect(self._filter_widget_changed)

        vl.addWidget(self.filter_widget_page)

        self.setLayout(vl)

    def _clear_all(self):
        for w in self.filter_widgets:
            w.clear()
        self.search_line_edit.clear()
        self.clear_all.emit()

    def set_starred(self, starred: bool):
        """
        Sets whether the starred filter should be active
        """
        if starred == self._starred:
            return

        self._starred = starred
        self._filter_widget_changed()

    def _show_advanced(self, show):
        if not show:
            for w in self.filter_widgets:
                w.collapse()
        self.advanced_stacked_widget.setVisible(show)
        self.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Preferred)
        self.advanced_stacked_widget.adjustSize()
        self.advanced_stacked_widget.setMinimumWidth(self.width())
        self.advanced_stacked_widget.setMinimumWidth(0)
        self.adjustSize()

    def _filter_widget_changed(self):
        # changes to filter parameters are deferred to a small timeout, to avoid
        # starting lots of queries while a user is mid-operation (such as dragging a slider)
        self._update_query_timeout.start(500)

        selected_data_types = self.data_type_filter_widget.data_types()

        if DataType.Rasters in selected_data_types or DataType.Grids in selected_data_types:
            # show resolution
            self.resolution_widget.setVisible(True)
        else:
            self.resolution_widget.setVisible(False)

        self.filter_widget_page.layout().update()


    def build_query(self) -> DataBrowserQuery:
        """
        Returns a query representing the current widget state
        """
        query = DataBrowserQuery()
        query.starred = self._starred
        query.order = self.sort_order

        if self.search_line_edit.text().strip():
            query.search = self.search_line_edit.text().strip()

        for w in self.filter_widgets:
            w.apply_constraints_to_query(query)

        return query

    def _update_query(self):
        self.filters_changed.emit()

    def set_logged_in(self, logged_in: bool):
        for w in self.filter_widgets:
            w.set_logged_in(logged_in)

    def set_facets(self, facets: dict):
        """
        Sets corresponding facets response for tweaking the widget choices
        """
        for w in self.filter_widgets:
            w.set_facets(facets)
