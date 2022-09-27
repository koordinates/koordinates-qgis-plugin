from qgis.PyQt.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QSpacerItem,
    QSizePolicy
)
from qgis.PyQt.QtCore import Qt
from qgis.PyQt.QtGui import QFontMetrics
from qgis.gui import (
    QgsRangeSlider,
    QgsDateEdit
)
from qgis.PyQt.QtCore import (
    QDate,
    QDateTime
)

from .filter_widget_combo_base import FilterWidgetComboBase
from ..api import DataBrowserQuery


class ClearableDateEdit(QgsDateEdit):

    def __init__(self, parent = None):
        super().__init__(parent)

        small_font = self.font()
        small_font.setPointSize(small_font.pointSize() - 2)
        self.setFont(small_font)

        self.setMinimumWidth(QFontMetrics(small_font).width('x') * 18)

        self._default_date = QDate()

    def set_default_date(self, date: QDate):
        self._default_date = date

    def default_date(self) -> QDate:
        return self._default_date

    def clear(self):
        self.setDate(self._default_date)


class DateFilterWidget(FilterWidgetComboBase):
    """
    Custom widget for date selection
    """

    def __init__(self, parent):
        super().__init__(parent)

        self.drop_down_widget = QWidget()
        vl = QVBoxLayout()
        published_date_label = QLabel('Published Date')
        bold_font = published_date_label.font()
        bold_font.setBold(True)
        published_date_label.setFont(bold_font)
        vl.addWidget(published_date_label)

        self.published_date_slider = QgsRangeSlider()
        self.published_date_slider.setMinimumHeight(self.fontMetrics().height())
        vl.addWidget(self.published_date_slider)

        hl = QHBoxLayout()
        self.min_published_date_edit = ClearableDateEdit()

        hl.addWidget(self.min_published_date_edit)
        hl.addStretch()
        self.max_published_date_edit = ClearableDateEdit()
        hl.addWidget(self.max_published_date_edit)

        vl.addLayout(hl)
        vl.addItem(QSpacerItem(1,self.fontMetrics().height(), QSizePolicy.Ignored, QSizePolicy.Expanding))

        updated_date_label = QLabel('Last Updated')
        updated_date_label.setFont(bold_font)
        vl.addWidget(updated_date_label)

        self.updated_date_slider = QgsRangeSlider()
        self.updated_date_slider.setMinimumHeight(self.fontMetrics().height())
        vl.addWidget(self.updated_date_slider)

        hl = QHBoxLayout()
        self.min_updated_date_edit = ClearableDateEdit()
        hl.addWidget(self.min_updated_date_edit)
        hl.addStretch()
        self.max_updated_date_edit = ClearableDateEdit()
        hl.addWidget(self.max_updated_date_edit)

        vl.addLayout(hl)

        self.drop_down_widget.setLayout(vl)
        self.set_contents_widget(self.drop_down_widget)

        self._block_range_slider_updates = False
        self._block_date_edit_updates = False
        self.published_date_slider.rangeChanged.connect(self._published_range_slider_changed)
        self.min_published_date_edit.dateChanged.connect(self._published_min_date_changed)
        self.max_published_date_edit.dateChanged.connect(self._published_max_date_changed)

        self.updated_date_slider.rangeChanged.connect(self._updated_range_slider_changed)
        self.min_updated_date_edit.dateChanged.connect(self._updated_min_date_changed)
        self.max_updated_date_edit.dateChanged.connect(self._updated_max_date_changed)

        self.set_published_range(QDate(2020,1,1), QDate(2022,9,27))
        self.set_updated_range(QDate(2021, 1, 1), QDate(2022, 9, 27))
        self.clear()

    def set_published_range(self, minimum: QDate, maximum: QDate):
        self.min_published_date_edit.set_default_date(minimum)
        self.max_published_date_edit.set_default_date(maximum)

        range_length = minimum.daysTo(maximum)
        self.published_date_slider.setRangeLimits(0, range_length)
        self._update_labels()

    def _published_range_slider_changed(self):
        if self._block_range_slider_updates:
            return

        min_date = self.min_published_date_edit.default_date()

        self._block_date_edit_updates = True
        self.min_published_date_edit.setDate(min_date.addDays(self.published_date_slider.lowerValue()))
        self.max_published_date_edit.setDate(min_date.addDays(self.published_date_slider.upperValue()))
        self._block_date_edit_updates = False
        self._update_labels()

    def _published_min_date_changed(self):
        if self._block_date_edit_updates:
            return

        min_date = self.min_published_date_edit.default_date()
        current_min = self.min_published_date_edit.date()
        self._block_range_slider_updates = True
        self.published_date_slider.setLowerValue(min_date.daysTo(current_min))
        self._block_range_slider_updates = False
        self._update_labels()

    def _published_max_date_changed(self):
        if self._block_date_edit_updates:
            return

        min_date = self.min_published_date_edit.default_date()
        current_max = self.max_published_date_edit.date()
        self._block_range_slider_updates = True
        self.published_date_slider.setUpperValue(min_date.daysTo(current_max))
        self._block_range_slider_updates = False
        self._update_labels()

    def set_updated_range(self, minimum: QDate, maximum: QDate):
        self.min_updated_date_edit.set_default_date(minimum)
        self.max_updated_date_edit.set_default_date(maximum)

        range_length = minimum.daysTo(maximum)
        self.updated_date_slider.setRangeLimits(0, range_length)
        self._update_labels()

    def _updated_range_slider_changed(self):
        if self._block_range_slider_updates:
            return

        min_date = self.min_updated_date_edit.default_date()

        self._block_date_edit_updates = True
        self.min_updated_date_edit.setDate(min_date.addDays(self.updated_date_slider.lowerValue()))
        self.max_updated_date_edit.setDate(min_date.addDays(self.updated_date_slider.upperValue()))
        self._block_date_edit_updates = False
        self._update_labels()

    def _updated_min_date_changed(self):
        if self._block_date_edit_updates:
            return

        min_date = self.min_updated_date_edit.default_date()
        current_min = self.min_updated_date_edit.date()
        self._block_range_slider_updates = True
        self.updated_date_slider.setLowerValue(min_date.daysTo(current_min))
        self._block_range_slider_updates = False
        self._update_labels()

    def _updated_max_date_changed(self):
        if self._block_date_edit_updates:
            return

        min_date = self.min_updated_date_edit.default_date()
        current_max = self.max_updated_date_edit.date()
        self._block_range_slider_updates = True
        self.updated_date_slider.setUpperValue(min_date.daysTo(current_max))
        self._block_range_slider_updates = False
        self._update_labels()

    def _update_labels(self):
        if (self.published_date_slider.lowerValue() != self.published_date_slider.minimum() or
            self.published_date_slider.upperValue() != self.published_date_slider.maximum()) and \
                (self.updated_date_slider.lowerValue() != self.updated_date_slider.minimum() or
                    self.updated_date_slider.upperValue() != self.updated_date_slider.maximum()):
            min_date = min(self.min_published_date_edit.date(), self.min_updated_date_edit.date())
            max_date = max(self.max_published_date_edit.date(), self.max_updated_date_edit.date())
            self.set_current_text('{} - {}'.format(min_date.toString(Qt.ISODate),
                                                   max_date.toString(Qt.ISODate)))
        elif self.published_date_slider.lowerValue() != self.published_date_slider.minimum() or \
                self.published_date_slider.upperValue() != self.published_date_slider.maximum():
            self.set_current_text('{} - {}'.format(self.min_published_date_edit.date().toString(Qt.ISODate),
                                                                  self.max_published_date_edit.date().toString(Qt.ISODate)))
        elif self.updated_date_slider.lowerValue() != self.updated_date_slider.minimum() or \
                self.updated_date_slider.upperValue() != self.updated_date_slider.maximum():
            self.set_current_text('{} - {}'.format(self.min_updated_date_edit.date().toString(Qt.ISODate),
                                                             self.max_updated_date_edit.date().toString(Qt.ISODate)))
        else:
            self.set_current_text('Date')

        if not self._block_changes:
            self.changed.emit()

    def clear(self):
        self.updated_date_slider.setRange(self.updated_date_slider.minimum(), self.updated_date_slider.maximum())
        self.published_date_slider.setRange(self.published_date_slider.minimum(), self.published_date_slider.maximum())
        self._update_labels()

    def should_show_clear(self):
        if self.published_date_slider.lowerValue() == self.published_date_slider.minimum() and \
                self.published_date_slider.upperValue() == self.published_date_slider.maximum() and \
                self.updated_date_slider.lowerValue() == self.updated_date_slider.minimum() and \
                self.updated_date_slider.upperValue() == self.updated_date_slider.maximum():
            return False

        return super().should_show_clear()

    def apply_constraints_to_query(self, query: DataBrowserQuery):
        if self.min_published_date_edit.date() != self.min_published_date_edit.default_date():
            query.created_minimum = QDateTime(self.min_published_date_edit.date())
        if self.max_published_date_edit.date() != self.max_published_date_edit.default_date():
            query.created_maximum = QDateTime(self.max_published_date_edit.date())
        if self.min_updated_date_edit.date() != self.min_updated_date_edit.default_date():
            query.updated_minimum = QDateTime(self.min_updated_date_edit.date())
        if self.max_updated_date_edit.date() != self.max_updated_date_edit.default_date():
            query.updated_maximum = QDateTime(self.max_updated_date_edit.date())

    def set_from_query(self, query: DataBrowserQuery):
        self._block_changes = True

        if query.created_minimum is not None:
            self.min_published_date_edit.setDate(query.created_minimum.date())
        else:
            self.published_date_slider.setLowerValue(self.published_date_slider.minimum())

        if query.created_maximum is not None:
            self.max_published_date_edit.setDate(query.created_maximum.date())
        else:
            self.published_date_slider.setUpperValue(self.published_date_slider.maximum())

        if query.updated_minimum is not None:
            self.min_updated_date_edit.setDate(query.updated_minimum.date())
        else:
            self.updated_date_slider.setLowerValue(self.updated_date_slider.minimum())

        if query.updated_maximum is not None:
            self.max_updated_date_edit.setDate(query.updated_maximum.date())
        else:
            self.updated_date_slider.setUpperValue(self.updated_date_slider.maximum())

        self._update_labels()
        self._block_changes = False
