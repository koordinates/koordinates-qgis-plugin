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


class FilterWidget(QWidget):
    filters_changed = pyqtSignal()
    show_advanced = pyqtSignal(bool)
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
        self.show_advanced_button.toggled.connect(self.show_advanced)

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

        # changes to filter parameters are deferred to a small timeout, to avoid
        # starting lots of queries while a user is mid-operation (such as dragging a slider)
        self._update_query_timeout = QTimer(self)
        self._update_query_timeout.setSingleShot(True)
        self._update_query_timeout.timeout.connect(self._update_query)

        self.search_line_edit.textChanged.connect(self._filter_widget_changed)

        self.setLayout(vl)

    def _clear_all(self):
        self.search_line_edit.clear()
        self.clear_all.emit()

    def set_show_advanced_button(self, show):
        self.show_advanced_button.setVisible(show)

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

        return query

    def _update_query(self):
        self.filters_changed.emit()

    def set_logged_in(self, logged_in: bool):
        pass

    def set_facets(self, facets: dict):
        """
        Sets corresponding facets response for tweaking the widget choices
        """
        pass
