from qgis.PyQt.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel
)
from qgis.gui import QgsRangeSlider

from .filter_widget_combo_base import FilterWidgetComboBase
from ..api import DataBrowserQuery

class ResolutionFilterWidget(FilterWidgetComboBase):
    """
    Custom widget for resolution selection
    """

    def __init__(self, parent):
        super().__init__(parent)

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
        if not self._block_changes:
            self.changed.emit()

    def clear(self):
        self.slider.setRange(self.slider.minimum(), self.slider.maximum())
        self._update_labels()

    def should_show_clear(self):
        if self.slider.lowerValue() == self.slider.minimum() and \
                self.slider.upperValue() == self.slider.maximum():
            return False

        return super().should_show_clear()

    def apply_constraints_to_query(self, query: DataBrowserQuery):
        if self.slider.lowerValue() != self.slider.minimum():
            query.minimum_resolution = self.slider.lowerValue()
        if self.slider.upperValue() != self.slider.maximum():
            query.maximum_resolution = self.slider.upperValue()

    def set_from_query(self, query: DataBrowserQuery):
        self._block_changes = True

        if query.minimum_resolution is not None:
            self.slider.setLowerValue(int(query.minimum_resolution))
        else:
            self.slider.setLowerValue(self.slider.minimum())
        if query.maximum_resolution is not None:
            self.slider.setUpperValue(int(query.maximum_resolution))
        else:
            self.slider.setUpperValue(self.slider.maximum())

        self._update_labels()
        self._block_changes = False
