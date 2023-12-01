from typing import Optional

from qgis.PyQt.QtCore import (
    Qt,
    QTimer,
    pyqtSignal,
    QSize
)
from qgis.PyQt.QtGui import (
    QFontMetrics,
    QPainter,
    QBrush,
    QColor,
    QPainterPath
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
from .publisher_filter_widget import PublisherFilterWidget
from .enums import FilterWidgetAppearance
from .flow_layout import FlowLayout
from .group_filter_widget import GroupFilterWidget
from .license_filter_widget import LicenseFilterWidget
from .resolution_filter_widget import ResolutionFilterWidget
from ..api import (
    DataBrowserQuery,
    DataType,
    Publisher
)


class AdvancedFilterWidget(QWidget):
    filters_changed = pyqtSignal()

    publisher_changed = pyqtSignal(object)

    CORNER_RADIUS = 4

    def __init__(self, parent):
        super().__init__(parent)

        self.should_show = False
        self.appearance = FilterWidgetAppearance.Horizontal

        # self.category_filter_widget = CategoryFilterWidget(self)
        self.data_type_filter_widget = DataTypeFilterWidget(self)
        self.publisher_filter_widget = PublisherFilterWidget(self)
        self.resolution_widget = ResolutionFilterWidget(self)
        self.date_filter_widget = DateFilterWidget(self)
        self.license_widget = LicenseFilterWidget(self)
        self.group_widget = GroupFilterWidget(self)
        self.access_widget = AccessFilterWidget(self)

        self.filter_widgets = (  # self.category_filter_widget,
            self.data_type_filter_widget,
            self.publisher_filter_widget,
            self.resolution_widget,
            self.date_filter_widget,
            self.license_widget,
            self.group_widget,
            self.access_widget,)

        min_filter_widget_width = QFontMetrics(self.font()).width('x') * 25
        # self.category_filter_widget.setMinimumWidth(min_filter_widget_width)
        for w in self.filter_widgets:
            w.setMinimumWidth(min_filter_widget_width)

        self.resolution_widget.hide()

        filter_widget_layout = FlowLayout()
        filter_widget_layout.setContentsMargins(10, 10, 10, 10)
        # filter_widget_layout.addWidget(self.category_filter_widget)
        for w in self.filter_widgets:
            filter_widget_layout.addWidget(w)

        # changes to filter parameters are deferred to a small timeout, to avoid
        # starting lots of queries while a user is mid-operation (such as dragging a slider)
        self._update_query_timeout = QTimer(self)
        self._update_query_timeout.setSingleShot(True)
        self._update_query_timeout.timeout.connect(self._update_query)

        for w in self.filter_widgets:
            w.changed.connect(self._filter_widget_changed)

        self.publisher_filter_widget.changed.connect(
            self._publisher_filter_changed
        )

        self.setLayout(filter_widget_layout)

    def sizeHint(self):
        return QSize(self.width(),
                     self.layout().heightForWidth(self.width()))

    def clear_all(self):
        for w in self.filter_widgets:
            w.clear()

    def set_appearance(self, appearance: FilterWidgetAppearance):
        self.appearance = appearance
        self.update()

    def _publisher_filter_changed(self):
        """
        Triggered when the current publisher filter is changed
        """
        self.publisher_changed.emit(
            self.publisher_filter_widget.current_publisher()
        )

    def set_publisher_filter_visible(self, visible: bool):
        """
        Sets whether the publisher filter is visible
        """
        self.publisher_filter_widget.setVisible(visible)
        self.publisher_filter_widget.updateGeometry()
        self.updateGeometry()

    def current_publisher(self) -> Optional[Publisher]:
        """
        Returns the selected publisher, if set
        """
        return self.publisher_filter_widget.current_publisher()

    def clear_publisher(self):
        """
        Clears any current publisher filter
        """
        self.publisher_filter_widget.clear()

    def paintEvent(self, event):
        option = QStyleOption()
        option.initFrom(self)

        painter = QStylePainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)

        painter.save()
        brush = QBrush(QColor(219, 219, 219))
        painter.setBrush(brush)
        painter.setPen(Qt.NoPen)

        if self.appearance == FilterWidgetAppearance.Horizontal:
            painter.drawRoundedRect(option.rect,
                                    self.CORNER_RADIUS,
                                    self.CORNER_RADIUS)
        else:
            path = QPainterPath()
            path.moveTo(option.rect.left(), option.rect.top())
            path.lineTo(option.rect.right(), option.rect.top())
            path.lineTo(option.rect.right(),
                        option.rect.bottom() - self.CORNER_RADIUS)
            path.arcTo(option.rect.right() - self.CORNER_RADIUS * 2,
                       option.rect.bottom() - self.CORNER_RADIUS * 2,
                       self.CORNER_RADIUS * 2,
                       self.CORNER_RADIUS * 2,
                       0, -90
                       )
            path.lineTo(option.rect.left() + self.CORNER_RADIUS,
                        option.rect.bottom())
            path.arcTo(option.rect.left(),
                       option.rect.bottom() - self.CORNER_RADIUS * 2,
                       self.CORNER_RADIUS * 2,
                       self.CORNER_RADIUS * 2,
                       270, -90
                       )
            path.lineTo(option.rect.left(),
                        option.rect.top())
            painter.drawPath(path)
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
            if w.isVisible():
                w.apply_constraints_to_query(query)

    def set_from_query(self, query: DataBrowserQuery):
        """
        Updates widgets to match a query
        """
        for w in self.filter_widgets:
            w.set_from_query(query)

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

    def collapse_all(self):
        """
        Collapses all expanded filter widgets
        """
        for w in self.filter_widgets:
            w.collapse()

    def show_advanced(self, show: bool):
        """
        Toggles whether the advanced filter controls are visible
        """
        if not show:
            self.collapse_all()
        self.setVisible(show)
