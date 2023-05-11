from enum import Enum, auto
from qgis.PyQt.QtCore import (
    Qt,
    QTimer,
    pyqtSignal
)
from qgis.PyQt.QtGui import (
    QFontMetrics,
    QPainter,
    QBrush,
    QColor
)
from qgis.PyQt.QtWidgets import (
    QWidget,
    QStylePainter,
    QStyleOption
)

from .access_filter_widget import AccessFilterWidget
#  from .category_filter_widget import CategoryFilterWidget
from .data_type_filter_widget import DataTypeFilterWidget
from .date_filter_widget import DateFilterWidget
from .flow_layout import FlowLayout
from .license_filter_widget import LicenseFilterWidget
from .resolution_filter_widget import ResolutionFilterWidget
from ..api import (
    DataBrowserQuery,
    DataType
)


class FilterWidgetAppearance(Enum):
    Horizontal = auto()
    Vertical = auto()


class AdvancedFilterWidget(QWidget):
    filters_changed = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)

        self.should_show = False
        self.appearance = FilterWidgetAppearance.Horizontal

        # self.category_filter_widget = CategoryFilterWidget(self)
        self.data_type_filter_widget = DataTypeFilterWidget(self)
        self.resolution_widget = ResolutionFilterWidget(self)
        self.date_filter_widget = DateFilterWidget(self)
        self.license_widget = LicenseFilterWidget(self)
        self.access_widget = AccessFilterWidget(self)

        min_filter_widget_width = QFontMetrics(self.font()).width('x') * 20
        # self.category_filter_widget.setMinimumWidth(min_filter_widget_width)
        self.data_type_filter_widget.setMinimumWidth(min_filter_widget_width)
        self.resolution_widget.setMinimumWidth(min_filter_widget_width)
        self.date_filter_widget.setMinimumWidth(min_filter_widget_width)
        self.license_widget.setMinimumWidth(min_filter_widget_width)
        self.access_widget.setMinimumWidth(min_filter_widget_width)

        self.resolution_widget.hide()

        filter_widget_layout = FlowLayout()
        filter_widget_layout.setContentsMargins(10, 10, 10, 10)
        # filter_widget_layout.addWidget(self.category_filter_widget)
        filter_widget_layout.addWidget(self.data_type_filter_widget)
        filter_widget_layout.addWidget(self.resolution_widget)
        filter_widget_layout.addWidget(self.date_filter_widget)
        filter_widget_layout.addWidget(self.license_widget)
        filter_widget_layout.addWidget(self.access_widget)

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

        self.setLayout(filter_widget_layout)

    def clear_all(self):
        for w in self.filter_widgets:
            w.clear()

    def set_appearance(self, appearance: FilterWidgetAppearance):
        self.appearance = appearance
        self.update()

    def paintEvent(self, event):
        option = QStyleOption()
        option.initFrom(self)

        painter = QStylePainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)

        painter.save()
        brush = QBrush(QColor(0, 0, 0, 38))
        painter.setBrush(brush)
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(option.rect, 4, 4)
        painter.restore()

        super().paintEvent(event)

    def _filter_widget_changed(self):
        # changes to filter parameters are deferred to a small timeout, to avoid
        # starting lots of queries while a user is mid-operation (such as dragging a slider)
        self._update_query_timeout.start(500)

        selected_data_types = self.data_type_filter_widget.data_types()

        if selected_data_types == {DataType.Rasters} or \
                selected_data_types == {DataType.Grids}:
            # show resolution
            self.resolution_widget.setVisible(True)
        else:
            self.resolution_widget.setVisible(False)

        self.layout().update()

    def apply_constraints_to_query(self, query: DataBrowserQuery):
        """
        Updates a query to reflect the current widget state
        """
        for w in self.filter_widgets:
            w.apply_constraints_to_query(query)

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

    def set_should_show(self, show):
        self.should_show = show

    def show_advanced(self, show):
        if not show:
            for w in self.filter_widgets:
                w.collapse()
        self.setVisible(show)
