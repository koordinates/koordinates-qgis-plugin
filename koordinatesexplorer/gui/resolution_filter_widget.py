from qgis.PyQt.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel
)
from qgis.gui import QgsRangeSlider

from .custom_combo_box import CustomComboBox


class ResolutionFilterWidget(CustomComboBox):
    """
    Custom widget for resolution selection
    """

    def __init__(self, parent):
        super().__init__(parent)
        self.set_show_clear_button(True)

        self.drop_down_widget = QWidget()
        vl = QVBoxLayout()
        self.slider = QgsRangeSlider()
        self.slider.setMinimumHeight(self.fontMetrics().height())
        vl.addWidget(self.slider)

        hl = QHBoxLayout()
        self.min_label = QLabel()
        hl.addWidget(self.min_label)
        hl.addStretch()
        hl.addWidget(QLabel('to'))
        hl.addStretch()
        self.max_label = QLabel()
        hl.addWidget(self.max_label)

        vl.addLayout(hl)

        self.drop_down_widget.setLayout(vl)
        self.set_contents_widget(self.drop_down_widget)

        self.slider.rangeChanged.connect(self._update_labels)

        self.set_range(0, 1000)
        self.clear()

    def set_range(self, minimum, maximum):
        self.slider.setRangeLimits(minimum, maximum)
        self._update_labels()

    def _update_labels(self):
        self.min_label.setText('{} m'.format(self.slider.lowerValue()))
        self.max_label.setText('{} m'.format(self.slider.upperValue()))
        if self.slider.lowerValue() == self.slider.minimum() and \
                self.slider.upperValue() == self.slider.maximum():
            self.set_current_text('Resolution')
        else:
            self.set_current_text('Resolution {} m - {} m'.format(self.slider.lowerValue(),
                                                                  self.slider.upperValue()))

    def clear(self):
        self.slider.setRange(self.slider.minimum(), self.slider.maximum())
        self._update_labels()

    def should_show_clear(self):
        if self.slider.lowerValue() == self.slider.minimum() and \
                self.slider.upperValue() == self.slider.maximum():
            return False

        return super().should_show_clear()
