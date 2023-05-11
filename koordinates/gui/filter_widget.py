from typing import Optional

from qgis.PyQt.QtCore import (
    QTimer,
    pyqtSignal
)
from qgis.PyQt.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QToolButton,
    QSizePolicy,
    QLabel
)
from qgis.gui import (
    QgsFilterLineEdit
)

from .gui_utils import GuiUtils
from ..api import (
    DataBrowserQuery,
    SortOrder
)
from .explore_tab_bar import ExploreTabBar
from .advanced_filter_widget import AdvancedFilterWidget


class FilterWidget(QWidget):
    filters_changed = pyqtSignal()
    clear_all = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)

        self._starred = False

        self.sort_order = SortOrder.Popularity

        self.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Preferred)

        vl = QVBoxLayout()
        vl.setSpacing(0)
        vl.setContentsMargins(0, 0, 0, 0)

        self.explore_tab_bar = ExploreTabBar()
        vl.addWidget(self.explore_tab_bar)
        self.explore_tab_bar.currentChanged.connect(self._explore_tab_changed)
        self.advanced_filter_widget = AdvancedFilterWidget(self)
        self.advanced_filter_widget.filters_changed.connect(self._filter_widget_changed)

        vl.addWidget(self.advanced_filter_widget)

        # changes to filter parameters are deferred to a small timeout, to avoid
        # starting lots of queries while a user is mid-operation (such as dragging a slider)
        self._update_query_timeout = QTimer(self)
        self._update_query_timeout.setSingleShot(True)
        self._update_query_timeout.timeout.connect(self._update_query)

        self.search_line_edit: Optional[QgsFilterLineEdit] = None

        self.setLayout(vl)

        self._explore_tab_changed(0)

    def set_search_line_edit(self, widget):
        self.search_line_edit = widget
        self.search_line_edit.textChanged.connect(self._filter_widget_changed)

    def _explore_tab_changed(self, tab_index: int):
        """
        Called when the active explore tab is changed
        """
        self.advanced_filter_widget.setVisible(
            tab_index == 1
        )
        self.updateGeometry()

    def _clear_all(self):
        self.search_line_edit.clear()
        self.advanced_filter_widget.clear_all()
        self.clear_all.emit()

    def set_starred(self, starred: bool):
        """
        Sets whether the starred filter should be active
        """
        if starred == self._starred:
            return

        self._starred = starred
        self._update_query()

    def _filter_widget_changed(self):
        # changes to filter parameters are deferred to a small timeout, to avoid
        # starting lots of queries while a user is mid-operation (such as dragging a slider)
        self._update_query_timeout.start(500)

    def build_query(self) -> DataBrowserQuery:
        """
        Returns a query representing the current widget state
        """
        query = DataBrowserQuery()
        query.starred = self._starred
        query.order = self.sort_order

        if self.search_line_edit.text().strip():
            query.search = self.search_line_edit.text().strip()

        self.advanced_filter_widget.apply_constraints_to_query(query)
        return query

    def _update_query(self):
        self.filters_changed.emit()

    def set_logged_in(self, logged_in: bool):
        self.advanced_filter_widget.set_logged_in(logged_in)

    def set_facets(self, facets: dict):
        """
        Sets corresponding facets response for tweaking the widget choices
        """
        self.advanced_filter_widget.set_facets(facets)
