from typing import Optional

from qgis.PyQt.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QRadioButton,
    QButtonGroup
)

from .filter_widget_combo_base import FilterWidgetComboBase
from ..api import (
    DataBrowserQuery
)


class GroupFilterWidget(FilterWidgetComboBase):
    """
    Custom widget for group based filtering
    """

    def __init__(self, parent):
        super().__init__(parent)
        self._current_context: Optional[str] = None

        self.drop_down_widget = QWidget()
        self.radio_layout = QVBoxLayout()

        self._radios = []

        self.button_group = QButtonGroup()
        self.button_group.setExclusive(False)
        self.button_group.buttonClicked.connect(self._group_member_clicked)

        self.drop_down_widget.setLayout(self.radio_layout)

        self.set_contents_widget(self.drop_down_widget)

        self.clear()

    def _group_member_clicked(self, clicked_button):
        self._block_changes += 1
        for radio in self._radios:
            if radio.isChecked() and radio != clicked_button:
                radio.setChecked(False)

        self._block_changes -= 1
        self._update_value()

    def _update_visible_frames(self):
        self.drop_down_widget.adjustSize()
        self._floating_widget.reflow()

    def clear(self):
        for radio in self._radios:
            radio.setChecked(False)

        self._update_visible_frames()
        self._update_value()

    def should_show_clear(self):
        return any(radio.isChecked() for radio in self._radios)

    def _update_value(self):
        text = 'Group'

        for radio in self._radios:
            if radio.isChecked():
                text = radio.text()

        self.set_current_text(text)
        if not self._block_changes:
            self.changed.emit()

    def apply_constraints_to_query(self, query: DataBrowserQuery):
        query.group = None
        for radio in self._radios:
            if radio.isChecked():
                query.group = radio.property('key')

    def set_from_query(self, query: DataBrowserQuery):
        self._block_changes += 1

        for radio in self._radios:
            if not query.group:
                radio.setChecked(False)
            else:
                radio.setChecked(radio.property('key') == query.group)

        self._update_value()
        self._update_visible_frames()
        self._block_changes -= 1

    def set_facets(self, facets: dict):
        groups = facets.get('group', [])
        new_context = facets.get('from')

        if new_context == self._current_context:
            return

        self._current_context = new_context
        for r in self._radios:
            r.deleteLater()
        self._radios = []

        if not groups:
            self.hide()
        else:
            self.show()
            for group in groups:
                radio = QRadioButton(group['name'])
                radio.setProperty('key', str(group['key']))
                self._radios.append(radio)
                self.button_group.addButton(radio)
                self.radio_layout.addWidget(radio)
