from qgis.PyQt.QtCore import pyqtSignal
from qgis.PyQt.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QRadioButton,
    QButtonGroup
)

from .custom_combo_box import CustomComboBox


class AccessFilterWidget(CustomComboBox):
    """
    Custom widget for access based filtering
    """

    changed = pyqtSignal()

    def __init__(self, parent):
        super().__init__(parent)
        self.set_show_clear_button(True)

        self._block_geometry_type_constraint_update = 0

        self.drop_down_widget = QWidget()
        vl = QVBoxLayout()

        self.public_radio = QRadioButton('Public')
        vl.addWidget(self.public_radio)

        self.private_radio = QRadioButton('Me')
        vl.addWidget(self.private_radio)

        self.access_group = QButtonGroup()
        self.access_group.addButton(self.public_radio)
        self.access_group.addButton(self.private_radio)

        self.drop_down_widget.setLayout(vl)

        self.set_contents_widget(self.drop_down_widget)

        self.access_group.buttonClicked.connect(self._update_value)

        self.clear()

    def _update_visible_frames(self):
        self.drop_down_widget.adjustSize()
        self._floating_widget.reflow()

    def clear(self):
        self.public_radio.setChecked(True)
        self._update_visible_frames()
        self._update_value()

    def should_show_clear(self):
        if self.public_radio.isChecked():
            return False

        return super().should_show_clear()

    def _update_value(self):
        text = 'Access'

        if self.private_radio.isChecked():
            text = 'Shared with me'

        self.set_current_text(text)
