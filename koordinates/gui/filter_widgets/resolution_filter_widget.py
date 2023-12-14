from typing import Optional
import math

from qgis.PyQt.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel
)

from .filter_widget_combo_base import FilterWidgetComboBase
from ...api import DataBrowserQuery
from .range_slider import RangeSlider


class ResolutionFilterWidget(FilterWidgetComboBase):
    """
    Custom widget for resolution selection
    """

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)

        self.drop_down_widget = QWidget()
        vl = QVBoxLayout()
        self.slider = RangeSlider()
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

        self._range = (0.03, 2000)
        self.slider.setRangeLimits(0, 100000)
        self.slider.setRange(self.slider.minimum(), self.slider.maximum())
        self._update_labels()

    @staticmethod
    def scale(value, domain, range):
        exp = 6.5
        return ((range[1] - range[0]) / math.pow(domain[1] - domain[0], exp)) * math.pow(
            value - domain[0], exp) + range[0]

    @staticmethod
    def unscale(value, domain, range):
        if range[1] == range[0]:
            return 0

        exp = 6.5

        try:
            return domain[0] + math.pow(
                (value - range[0]) * math.pow(domain[1] - domain[0], exp) / (range[1] - range[0])
                , 1 / exp
            )
        except ValueError:
            return 0

    def map_slider_value_to_resolution(self, value):
        return round(self.scale(
            value,
            (0, 100000),
            self._range), 2)

    def map_value_to_slider(self, value):
        if self.map_slider_value_to_resolution(0) == value:
            return 0

        vv = int(self.unscale(value, (0, 100000), self._range))

        return vv

    def current_range(self):
        return (self.map_slider_value_to_resolution(self.slider.lowerValue()),
                self.map_slider_value_to_resolution(self.slider.upperValue()))

    def _update_labels(self):
        lower, upper = self.current_range()
        self.min_label.setText('{} m'.format(lower))
        self.max_label.setText('{} m'.format(upper))
        if self.slider.lowerValue() == self.slider.minimum() and \
                self.slider.upperValue() == self.slider.maximum():
            self.set_current_text('Resolution')
        else:
            self.set_current_text('Resolution {} m - {} m'.format(lower,
                                                                  upper))
        if not self._block_changes:
            self.changed.emit()

    def clear(self):
        if self.slider.lowerValue() == self.slider.minimum() and \
                self.slider.upperValue() == self.slider.maximum():
            return

        self._block_changes += 1
        self.slider.setRange(self.slider.minimum(), self.slider.maximum())
        self._block_changes -= 1
        self._update_labels()

    def should_show_clear(self):
        if self.slider.lowerValue() == self.slider.minimum() and \
                self.slider.upperValue() == self.slider.maximum():
            return False

        return super().should_show_clear()

    def apply_constraints_to_query(self, query: DataBrowserQuery):
        mapped_lower_value =self.map_slider_value_to_resolution(self.slider.lowerValue())
        mapped_minimum = self.map_slider_value_to_resolution(self.slider.minimum())
        if mapped_lower_value != mapped_minimum:
            query.minimum_resolution = mapped_lower_value
        else:
            query.minimum_resolution = None
        mapped_upper_value = self.map_slider_value_to_resolution(self.slider.upperValue())
        mapped_maximum = self.map_slider_value_to_resolution(self.slider.maximum())
        if mapped_upper_value != mapped_maximum:
            query.maximum_resolution = mapped_upper_value
        else:
            query.maximum_resolution = None

    def set_from_query(self, query: DataBrowserQuery):
        self._block_changes += 1

        if query.minimum_resolution is not None:
            self.slider.setLowerValue(
                self.map_value_to_slider(query.minimum_resolution)
            )
        else:
            self.slider.setLowerValue(self.slider.minimum())
        if query.maximum_resolution is not None:
            self.slider.setUpperValue(
                self.map_value_to_slider(query.maximum_resolution))
        else:
            self.slider.setUpperValue(self.slider.maximum())

        self._update_labels()
        self._block_changes -= 1

    def set_facets(self, facets: dict):
        min_res = facets.get('raster_resolution', {}).get('min')
        max_res = facets.get('raster_resolution', {}).get('max')

        prev_range = list(self.current_range())
        if prev_range[0] == self._range[0]:
            prev_range[0] = None
        if prev_range[1] == self._range[1]:
            prev_range[1] = None

        if min_res is not None and max_res is not None:
            self._range = (min_res, max_res)
            new_range = prev_range[:]
            if prev_range[0] is not None:
                new_range[0] = max(prev_range[0], min_res)
            else:
                new_range[0] = min_res
            if prev_range[1] is not None:
                new_range[1] = min(prev_range[1], max_res)
            else:
                new_range[1] = max_res
        else:
            self._range = (0.03, 2000)
            new_range = self._range

        self._block_changes += 1
        slider_min = self.map_value_to_slider(new_range[0])
        slider_max = self.map_value_to_slider(new_range[1])
        self.slider.setRange(slider_min, slider_max)

        self._update_labels()
        self._block_changes -= 1
