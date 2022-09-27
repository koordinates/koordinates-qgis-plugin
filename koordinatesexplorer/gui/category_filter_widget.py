from qgis.PyQt.QtCore import pyqtSignal
from qgis.PyQt.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QRadioButton,
    QButtonGroup
)

from .filter_widget_combo_base import FilterWidgetComboBase
from ..api import (
    DataBrowserQuery,
    AccessType,
    KoordinatesClient
)

class CategoryFilterWidget(FilterWidgetComboBase):
    """
    Custom widget for category based filtering
    """

    def __init__(self, parent):
        super().__init__(parent)

        self.drop_down_widget = QWidget()
        vl = QVBoxLayout()

        self.all_categories_radio = QRadioButton('All categories')
        self.category_radios = []
        self.category_group = QButtonGroup()
        self.category_group.addButton(self.all_categories_radio)
        vl.addWidget(self.all_categories_radio)

        self.drop_down_widget.setLayout(vl)

        self.set_contents_widget(self.drop_down_widget)

        self.category_group.buttonClicked.connect(self._update_value)

        self.clear()

    def set_logged_in(self, logged_in: bool):
        if not logged_in:
            return

        for w in self.category_radios:
            w.deleteLater()

        self.category_radios = []

        for c in KoordinatesClient.instance().categories():
            name = c['name']
            label = name.replace('&', '&&')
            r = QRadioButton(label)
            r._key = c['key']
            r._name = name

            self.drop_down_widget.layout().addWidget(r)
            self.category_group.addButton(r)

            self.category_radios.append(r)

        self.drop_down_widget.adjustSize()
        self._floating_widget.reflow()


    def _update_visible_frames(self):
        self.drop_down_widget.adjustSize()
        self._floating_widget.reflow()

    def clear(self):
        self.all_categories_radio.setChecked(True)
        self._update_visible_frames()
        self._update_value()

    def should_show_clear(self):
        if self.all_categories_radio.isChecked():
            return False

        for r in self.category_radios:
            if r.isChecked():
                return True

        return super().should_show_clear()

    def _update_value(self):
        text = 'Category'

        if not self.all_categories_radio.isChecked():
            for r in self.category_radios:
                if r.isChecked():
                    text = r._name
                    break

        self.set_current_text(text)
        if not self._block_changes:
            self.changed.emit()

    def apply_constraints_to_query(self, query: DataBrowserQuery):
        if not self.all_categories_radio.isChecked():
            for r in self.category_radios:
                if r.isChecked():
                    query.category = r._key

    def set_from_query(self, query: DataBrowserQuery):
        self._block_changes = True

        if not query.category:
            self.all_categories_radio.setChecked(True)
        else:
            for r in self.category_radios:
                if query.category == r._key:
                    r.setChecked(True)
                    break

        self._update_value()
        self._update_visible_frames()
        self._block_changes = False
