from typing import Optional

from qgis.PyQt.QtCore import (
    QTimer,
    pyqtSignal,
    QSize
)
from qgis.PyQt.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QButtonGroup,
    QSizePolicy
)
from qgis.gui import (
    QgsFilterLineEdit
)

from .advanced_filter_widget import AdvancedFilterWidget
from .enums import (
    TabStyle,
    FilterWidgetAppearance,
    ExploreMode
)
from .explore_tab_bar import (
    ExploreTabBar,
    ExploreTabButton
)
from .gui_utils import GuiUtils
from ..api import (
    DataBrowserQuery,
    SortOrder,
    DataType,
    AccessType,
    ExplorePanel
)
from .results_panel.filter_banner import PublisherFilterBannerWidget


class FilterWidget(QWidget):
    filters_changed = pyqtSignal()
    explore = pyqtSignal(ExplorePanel)
    explore_publishers = pyqtSignal()
    clear_all = pyqtSignal()

    def __init__(self, parent):
        super().__init__(parent)

        self._starred = False

        self._wide_mode = False

        self.sort_order = SortOrder.Popularity

        self.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Minimum)

        vl = QVBoxLayout()
        vl.setSpacing(0)
        vl.setContentsMargins(0, 0, 0, 0)

        narrow_layout = QVBoxLayout()
        narrow_layout.setContentsMargins(0, 0, 0, 0)
        narrow_layout.setSpacing(0)
        self.explore_tab_bar = ExploreTabBar()
        self.explore_tab_bar.setSizePolicy(QSizePolicy.Ignored,
                                           QSizePolicy.Fixed)
        narrow_layout.addWidget(self.explore_tab_bar)

        self.explore_tab_bar.currentChanged.connect(self._explore_tab_changed)
        self.advanced_filter_widget = AdvancedFilterWidget(self)
        self.advanced_filter_widget.filters_changed.connect(
            self._filter_widget_changed)

        narrow_layout.addWidget(self.advanced_filter_widget)
        self.publisher_container = QVBoxLayout()
        self.publisher_container.setContentsMargins(0, 12, 0, 12)
        self.publisher_widget = QWidget()
        self.publisher_widget.setLayout(self.publisher_container)
        self.publisher_widget.hide()
        narrow_layout.addWidget(self.publisher_widget)

        self._publisher_banner: Optional[PublisherFilterBannerWidget] = None

        self.narrow_widget = QWidget()
        self.narrow_widget.setLayout(narrow_layout)

        vl.addWidget(self.narrow_widget)

        # changes to filter parameters are deferred to a small timeout, to avoid
        # starting lots of queries while a user is mid-operation (such as dragging a slider)
        self._update_query_timeout = QTimer(self)
        self._update_query_timeout.setSingleShot(True)
        self._update_query_timeout.timeout.connect(self._update_query)

        self.popular_button = ExploreTabButton()
        self.popular_button.setIcon(GuiUtils.get_icon('popular.svg'))
        self.popular_button.setText(self.tr('Popular'))

        self.browse_button = ExploreTabButton()
        self.browse_button.setIcon(GuiUtils.get_icon('browse.svg'))
        self.browse_button.setText(self.tr('Browse'))
        self.browse_button.bottom_tab_style = TabStyle.Flat

        self.publishers_button = ExploreTabButton()
        self.publishers_button.setIcon(GuiUtils.get_icon('publishers.svg'))
        self.publishers_button.setText(self.tr('Publishers'))

        self.recent_button = ExploreTabButton()
        self.recent_button.setIcon(GuiUtils.get_icon('recent.svg'))
        self.recent_button.setText(self.tr('Recent'))

        button_group = QButtonGroup(self)
        button_group.addButton(self.popular_button)
        button_group.addButton(self.browse_button)
        button_group.addButton(self.publishers_button)
        button_group.addButton(self.recent_button)

        button_group.buttonToggled.connect(self._explore_button_toggled)

        wide_mode_layout = QVBoxLayout()
        wide_mode_layout.setContentsMargins(0, 0, 0, 0)
        wide_mode_layout.setSpacing(0)
        wide_mode_layout.addWidget(self.popular_button)
        wide_mode_layout.addWidget(self.publishers_button)
        wide_mode_layout.addWidget(self.recent_button)
        wide_mode_layout.addWidget(self.browse_button)
        self.wide_mode_filter_layout = QVBoxLayout()
        self.wide_mode_filter_layout.setContentsMargins(0, 0, 0, 0)
        wide_mode_layout.addLayout(self.wide_mode_filter_layout)
        wide_mode_layout.addStretch(1)

        self.wide_widget = QWidget()
        self.wide_widget.setLayout(wide_mode_layout)
        self.wide_widget.hide()
        vl.addWidget(self.wide_widget)
        self.setLayout(vl)

        self.search_line_edit: Optional[QgsFilterLineEdit] = None

        self._explore_tab_changed(0)

    def sizeHint(self):
        if not self._wide_mode:
            width = self.width()
            height = self.explore_tab_bar.sizeHint().height() \
                if self.explore_tab_bar.isVisible() else 0
            if self.advanced_filter_widget.isVisible():
                height += self.advanced_filter_widget.sizeHint().height()
        else:
            width = self.advanced_filter_widget.sizeHint().width()
            height = self.browse_button.sizeHint().height() \
                if self.browse_button.isVisible() else 0
            height += self.popular_button.sizeHint().height()
            if self.advanced_filter_widget.isVisible():
                height += self.advanced_filter_widget.sizeHint().height()

        if self._publisher_banner:
            height += self.publisher_container.sizeHint().height()

        return QSize(width, height)

    def set_wide_mode(self, wide_mode: bool):
        if self._wide_mode == wide_mode:
            return

        self._wide_mode = wide_mode
        if self._wide_mode:
            self.narrow_widget.layout().removeWidget(
                self.advanced_filter_widget)
            self.narrow_widget.layout().removeWidget(
                self.publisher_widget)
            self.wide_mode_filter_layout.addWidget(self.advanced_filter_widget)
            self.wide_mode_filter_layout.addWidget(self.publisher_widget)
            self.wide_widget.show()
            self.narrow_widget.hide()
            self.advanced_filter_widget.set_appearance(
                FilterWidgetAppearance.Vertical
            )
        else:
            self.wide_mode_filter_layout.removeWidget(
                self.advanced_filter_widget)
            self.wide_mode_filter_layout.removeWidget(
                self.publisher_widget)
            self.narrow_widget.layout().addWidget(self.advanced_filter_widget)
            self.narrow_widget.layout().addWidget(self.publisher_widget)
            self.wide_widget.hide()
            self.narrow_widget.show()
            self.advanced_filter_widget.set_appearance(
                FilterWidgetAppearance.Horizontal
            )

        self.updateGeometry()

    def set_search_line_edit(self, widget):
        self.search_line_edit = widget
        self.search_line_edit.textChanged.connect(self._search_text_changed)

    def _search_text_changed(self):
        if self.search_line_edit.text().strip():
            self.set_explore_mode(ExploreMode.Browse)
            self._filter_widget_changed()

    def set_is_browse_tab(self, is_browse: bool):
        """
        Sets whether the current context tab is the browse tab
        """
        self.explore_tab_bar.setVisible(is_browse)
        self.browse_button.setVisible(is_browse)
        self.popular_button.setVisible(is_browse)
        self.publishers_button.setVisible(is_browse)
        self.recent_button.setVisible(is_browse)
        self.advanced_filter_widget.set_publisher_filter_visible(
            is_browse
        )
        if not is_browse:
            self.advanced_filter_widget.set_appearance(
                FilterWidgetAppearance.Horizontal
            )
        else:
            if self._wide_mode:
                self.advanced_filter_widget.set_appearance(
                    FilterWidgetAppearance.Vertical)
            else:
                self.advanced_filter_widget.set_appearance(
                    FilterWidgetAppearance.Horizontal)

    def _explore_tab_changed(self, tab_index: int):
        """
        Called when the active explore tab is changed
        """
        if tab_index == 0:
            self.set_explore_mode(ExploreMode.Popular)
        elif tab_index == 1:
            self.set_explore_mode(ExploreMode.Browse)
        elif tab_index == 2:
            self.set_explore_mode(ExploreMode.Publishers)
        elif tab_index == 3:
            self.set_explore_mode(ExploreMode.Recent)

    def _explore_button_toggled(self, button, checked):
        if not checked:
            return

        if button == self.popular_button:
            self.set_explore_mode(ExploreMode.Popular)
        elif button == self.browse_button:
            self.set_explore_mode(ExploreMode.Browse)
        elif button == self.publishers_button:
            self.set_explore_mode(ExploreMode.Publishers)
        elif button == self.recent_button:
            self.set_explore_mode(ExploreMode.Recent)

    def explore_mode(self) -> ExploreMode:
        tab_index = self.explore_tab_bar.currentIndex()
        if tab_index == 0:
            return ExploreMode.Popular
        elif tab_index == 1:
            return ExploreMode.Browse
        elif tab_index == 2:
            return ExploreMode.Publishers
        else:
            return ExploreMode.Recent

    def set_explore_mode(self, mode: ExploreMode):
        show_filters = mode == ExploreMode.Browse
        self.advanced_filter_widget.setVisible(
            show_filters
        )
        if show_filters:
            self.advanced_filter_widget.updateGeometry()

        if mode in (
                ExploreMode.Popular,
                ExploreMode.Recent) and self.search_line_edit:
            self.search_line_edit.clear()

        if mode == ExploreMode.Popular:
            self.explore_tab_bar.setCurrentIndex(0)
            self.popular_button.setChecked(True)
        elif mode == ExploreMode.Browse:
            self.explore_tab_bar.setCurrentIndex(1)
            self.browse_button.setChecked(True)
        elif mode == ExploreMode.Publishers:
            self.explore_tab_bar.setCurrentIndex(2)
            self.publishers_button.setChecked(True)
        elif mode == ExploreMode.Recent:
            self.explore_tab_bar.setCurrentIndex(3)
            self.recent_button.setChecked(True)

        self.updateGeometry()
        if mode == ExploreMode.Popular:
            self.explore.emit(ExplorePanel.Popular)
        elif mode == ExploreMode.Recent:
            self.explore.emit(ExplorePanel.Recent)
        elif mode == ExploreMode.Publishers:
            self.explore_publishers.emit()
        else:
            self._update_query()

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
        mode = self.explore_mode()
        if mode == ExploreMode.Browse:
            query.starred = self._starred
            query.order = self.sort_order

            if self.search_line_edit.text().strip():
                query.search = self.search_line_edit.text().strip()

            self.advanced_filter_widget.apply_constraints_to_query(query)
        elif mode == ExploreMode.Popular:
            query.order = SortOrder.Popularity
            query.access_type = AccessType.Public
            query.data_types = {DataType.Tables,
                                DataType.Vectors,
                                DataType.Rasters,
                                DataType.Grids,
                                DataType.PointClouds}
        elif mode == ExploreMode.Recent:
            query.order = SortOrder.RecentlyUpdated
            query.access_type = AccessType.Public
            query.data_types = {DataType.Tables,
                                DataType.Vectors,
                                DataType.Rasters,
                                DataType.Grids,
                                DataType.PointClouds}

        return query

    def set_from_query(self, query: DataBrowserQuery):
        """
        Update widgets to match a query
        """
        self.advanced_filter_widget.set_from_query(query)

    def _update_query(self):
        self.filters_changed.emit()

        publisher = self.advanced_filter_widget.current_publisher()
        if publisher:
            if self._publisher_banner and \
                    self._publisher_banner.publisher.id() == publisher.id():
                pass
            else:
                if self._publisher_banner:
                    self._publisher_banner.deleteLater()

                self._publisher_banner = PublisherFilterBannerWidget(publisher)
                self.publisher_container.addWidget(self._publisher_banner)
                self.publisher_widget.show()
                self._publisher_banner.closed.connect(self._remove_publisher_filter)
                self.updateGeometry()

        elif self._publisher_banner:
            self._publisher_banner.deleteLater()
            self._publisher_banner = None

            self.publisher_widget.hide()
            self.updateGeometry()

    def _remove_publisher_filter(self):
        self.advanced_filter_widget.clear_publisher()

    def set_logged_in(self, logged_in: bool):
        self.advanced_filter_widget.set_logged_in(logged_in)

    def set_facets(self, facets: dict):
        """
        Sets corresponding facets response for tweaking the widget choices
        """
        self.advanced_filter_widget.set_facets(facets)
