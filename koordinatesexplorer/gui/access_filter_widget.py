from qgis.PyQt.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QRadioButton,
    QButtonGroup
)

from .filter_widget_combo_base import FilterWidgetComboBase
from ..api import (
    DataBrowserQuery,
    AccessType
)


class AccessFilterWidget(FilterWidgetComboBase):
    """
    Custom widget for access based filtering
    """

    def __init__(self, parent):
        super().__init__(parent)

        self.drop_down_widget = QWidget()
        vl = QVBoxLayout()

        self.public_radio = QRadioButton('Public')
        vl.addWidget(self.public_radio)

        self.private_radio = QRadioButton('Me')
        vl.addWidget(self.private_radio)

        self.access_group = QButtonGroup()
        self.access_group.addButton(self.public_radio)
        self.access_group.addButton(self.private_radio)
        self.access_group.setExclusive(False)
        self.access_group.buttonClicked.connect(self._access_group_member_clicked)

        self.drop_down_widget.setLayout(vl)

        self.set_contents_widget(self.drop_down_widget)

        self.clear()

    def _access_group_member_clicked(self, clicked_button):
        self._block_changes += 1
        for radio in (self.public_radio,
                      self.private_radio):
            if radio.isChecked() and radio != clicked_button:
                radio.setChecked(False)

        self._block_changes -= 1
        self._update_value()

    def _update_visible_frames(self):
        self.drop_down_widget.adjustSize()
        self._floating_widget.reflow()

    def clear(self):
        self.public_radio.setChecked(False)
        self.private_radio.setChecked(False)
        self._update_visible_frames()
        self._update_value()

    def should_show_clear(self):
        if not self.public_radio.isChecked() and not self.private_radio.isChecked():
            return False

        return super().should_show_clear()

    def _update_value(self):
        text = 'Access'

        if self.public_radio.isChecked():
            text = 'Only public data'
        elif self.private_radio.isChecked():
            text = 'Shared with me'

        self.set_current_text(text)
        if not self._block_changes:
            self.changed.emit()

    def apply_constraints_to_query(self, query: DataBrowserQuery):
        if self.public_radio.isChecked():
            query.access_type = AccessType.Public
        elif self.private_radio.isChecked():
            query.access_type = AccessType.Private
        else:
            query.access_type = None

    def set_from_query(self, query: DataBrowserQuery):
        self._block_changes += 1

        self.public_radio.setChecked(query.access_type == AccessType.Public)
        self.private_radio.setChecked(query.access_type == AccessType.Private)

        self._update_value()
        self._update_visible_frames()
        self._block_changes -= 1
