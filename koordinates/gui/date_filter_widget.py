from typing import Optional
from qgis.PyQt.QtCore import (
    Qt,
    QDate,
    QDateTime
)
from qgis.PyQt.QtGui import QFontMetrics
from qgis.PyQt.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QSpacerItem,
    QSizePolicy
)
from qgis.gui import (
    QgsDateEdit
)

from .filter_widget_combo_base import FilterWidgetComboBase
from ..api import DataBrowserQuery
from .range_slider import RangeSlider

DATE_FORMAT = 'dd MMM yyyy'


class ClearableDateEdit(QgsDateEdit):

    def __init__(self, parent=None):
        super().__init__(parent)

        small_font = self.font()
        small_font.setPointSize(small_font.pointSize() - 2)
        self.setFont(small_font)

        # need to set minimum width of widget to fit the full date string, plus extra
        # space for controls
        self.setMinimumWidth(QFontMetrics(small_font).width(DATE_FORMAT + 'xxxxxxxxx'))
        self.setDisplayFormat(DATE_FORMAT)

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

        self.published_date_slider = RangeSlider()
        self.published_date_slider.setMinimumHeight(self.fontMetrics().height())
        vl.addWidget(self.published_date_slider)

        hl = QHBoxLayout()
        self.min_published_date_edit = ClearableDateEdit()

        hl.addWidget(self.min_published_date_edit)
        hl.addStretch()
        self.max_published_date_edit = ClearableDateEdit()
        self.max_published_date_edit.setDate(QDate.currentDate())
        self.max_published_date_edit.setMaximumDate(QDate.currentDate())

        hl.addWidget(self.max_published_date_edit)

        vl.addLayout(hl)
        vl.addItem(
            QSpacerItem(1,
                        self.fontMetrics().height(),
                        QSizePolicy.Ignored,
                        QSizePolicy.Expanding
                        )
        )

        updated_date_label = QLabel('Last Updated')
        updated_date_label.setFont(bold_font)
        vl.addWidget(updated_date_label)

        self.updated_date_slider = RangeSlider()
        self.updated_date_slider.setMinimumHeight(self.fontMetrics().height())
        vl.addWidget(self.updated_date_slider)

        hl = QHBoxLayout()
        self.min_updated_date_edit = ClearableDateEdit()
        hl.addWidget(self.min_updated_date_edit)
        hl.addStretch()
        self.max_updated_date_edit = ClearableDateEdit()
        self.max_updated_date_edit.setDate(QDate.currentDate())
        self.max_updated_date_edit.setMaximumDate(QDate.currentDate())
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

        self.set_published_range(QDate(2000, 1, 1), QDate.currentDate())
        self.set_updated_range(QDate(2000, 1, 1), QDate.currentDate())

        self.clear()

    def set_published_range(self, minimum: QDate, maximum: QDate):
        self._block_changes += 1

        prev_min_published = self.min_published_date_edit.date()
        if prev_min_published == self.min_published_date_edit.default_date():
            prev_min_published = None

        prev_max_published = self.max_published_date_edit.date()
        if prev_max_published == self.max_published_date_edit.default_date():
            prev_max_published = None

        self.min_published_date_edit.set_default_date(minimum)
        self.max_published_date_edit.set_default_date(maximum)

        range_length = minimum.daysTo(maximum)
        self._block_range_slider_updates = True
        self.published_date_slider.setRangeLimits(0, range_length)
        self._block_range_slider_updates = False

        self.min_published_date_edit.setMinimumDate(minimum)
        self.max_published_date_edit.setMinimumDate(minimum)

        if prev_min_published and prev_min_published < minimum:
            prev_min_published = minimum
        if prev_max_published and prev_max_published < minimum:
            prev_max_published = minimum

        self.min_published_date_edit.setMaximumDate(maximum)
        self.max_published_date_edit.setMaximumDate(maximum)
        if prev_min_published and prev_min_published > maximum:
            prev_min_published = maximum
        if prev_max_published and prev_max_published > maximum:
            prev_max_published = maximum

        changed = False
        self._block_range_slider_updates = True

        if prev_min_published and self.min_published_date_edit.date() != prev_min_published:
            self.min_published_date_edit.setDate(prev_min_published)
            changed = True
        elif not prev_min_published:
            self.min_published_date_edit.setDate(minimum)

        if prev_max_published and self.max_published_date_edit.date() != prev_max_published:
            self.max_published_date_edit.setDate(prev_max_published)
            changed = True
        elif not prev_max_published:
            self.max_published_date_edit.setDate(maximum)

        self._block_range_slider_updates = True
        self.published_date_slider.setLowerValue(
            minimum.daysTo(self.min_published_date_edit.date())
        )
        self.published_date_slider.setUpperValue(
            minimum.daysTo(self.max_published_date_edit.date())
        )
        self._block_range_slider_updates = False

        self._update_labels()

        self._block_changes -= 1
        if changed:
            self.changed.emit()

    def _published_range_slider_changed(self):
        if self._block_range_slider_updates:
            return

        min_date = self.min_published_date_edit.default_date()

        self._block_date_edit_updates = True
        self.min_published_date_edit.setDate(
            min_date.addDays(self.published_date_slider.lowerValue())
        )
        self.max_published_date_edit.setDate(
            min_date.addDays(self.published_date_slider.upperValue())
        )
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
        self._block_changes += 1

        prev_min_updated = self.min_updated_date_edit.date()
        if prev_min_updated == self.min_updated_date_edit.default_date():
            prev_min_updated = None

        prev_max_updated = self.max_updated_date_edit.date()
        if prev_max_updated == self.max_updated_date_edit.default_date():
            prev_max_updated = None

        self.min_updated_date_edit.set_default_date(minimum)
        self.max_updated_date_edit.set_default_date(maximum)

        range_length = minimum.daysTo(maximum)
        self._block_range_slider_updates = True
        self.updated_date_slider.setRangeLimits(0, range_length)
        self._block_range_slider_updates = False

        self.min_updated_date_edit.setMinimumDate(minimum)
        self.max_updated_date_edit.setMinimumDate(minimum)

        if prev_min_updated and prev_min_updated < minimum:
            prev_min_updated = minimum
        if prev_max_updated and prev_max_updated < minimum:
            prev_max_updated = minimum

        self.min_updated_date_edit.setMaximumDate(maximum)
        self.max_updated_date_edit.setMaximumDate(maximum)
        if prev_min_updated and prev_min_updated > maximum:
            prev_min_updated = maximum
        if prev_max_updated and prev_max_updated > maximum:
            prev_max_updated = maximum

        changed = False
        self._block_range_slider_updates = True

        if prev_min_updated and self.min_updated_date_edit.date() != prev_min_updated:
            self.min_updated_date_edit.setDate(prev_min_updated)
            changed = True
        elif not prev_min_updated:
            self.min_updated_date_edit.setDate(minimum)

        if prev_max_updated and self.max_updated_date_edit.date() != prev_max_updated:
            self.max_updated_date_edit.setDate(prev_max_updated)
            changed = True
        elif not prev_max_updated:
            self.max_updated_date_edit.setDate(maximum)

        self._block_range_slider_updates = True
        self.updated_date_slider.setLowerValue(minimum.daysTo(self.min_updated_date_edit.date()))
        self.updated_date_slider.setUpperValue(minimum.daysTo(self.max_updated_date_edit.date()))
        self._block_range_slider_updates = False

        self._update_labels()

        self._block_changes -= 1
        if changed:
            self.changed.emit()

    def _updated_range_slider_changed(self):
        if self._block_range_slider_updates:
            return

        min_date = self.min_updated_date_edit.default_date()

        self._block_date_edit_updates = True
        self.min_updated_date_edit.setDate(
            min_date.addDays(self.updated_date_slider.lowerValue())
        )
        self.max_updated_date_edit.setDate(
            min_date.addDays(self.updated_date_slider.upperValue())
        )
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
            self.set_current_text('{} - {}'.format(min_date.toString(DATE_FORMAT),
                                                   max_date.toString(DATE_FORMAT)))
        elif self.published_date_slider.lowerValue() != self.published_date_slider.minimum() or \
                self.published_date_slider.upperValue() != self.published_date_slider.maximum():
            self.set_current_text('{} - {}'.format(
                self.min_published_date_edit.date().toString(DATE_FORMAT),
                self.max_published_date_edit.date().toString(DATE_FORMAT))
            )
        elif self.updated_date_slider.lowerValue() != self.updated_date_slider.minimum() or \
                self.updated_date_slider.upperValue() != self.updated_date_slider.maximum():
            self.set_current_text('{} - {}'.format(
                self.min_updated_date_edit.date().toString(DATE_FORMAT),
                self.max_updated_date_edit.date().toString(DATE_FORMAT))
            )
        else:
            self.set_current_text('Date')

        if not self._block_changes:
            self.changed.emit()

    def set_facets(self, facets: dict):

        def _str_to_date(val: str) -> Optional[str]:
            if not val:
                return None
            return QDateTime.fromString(val, Qt.ISODate).date()

        min_updated = _str_to_date(facets.get('updated_at', {}).get('min'))
        max_updated = _str_to_date(facets.get('updated_at', {}).get('max'))
        min_created = _str_to_date(facets.get('created_at', {}).get('min'))
        max_created = _str_to_date(facets.get('created_at', {}).get('max'))

        if min_updated and max_updated:
            self.set_updated_range(min_updated, max_updated)
        if min_created and max_created:
            self.set_published_range(min_created, max_created)

    def set_created_limits(self, min_date: Optional[QDate], max_date: Optional[QDate]):
        prev_min_created = self.min_published_date_edit.date()
        prev_max_created = self.max_published_date_edit.date()

        if min_date:
            self.min_published_date_edit.setMinimumDate(min_date)
            self.max_published_date_edit.setMinimumDate(min_date)
            if prev_min_created < min_date:
                prev_min_created = min_date
            if prev_max_created < min_date:
                prev_max_created = min_date
        if max_date:
            self.min_published_date_edit.setMaximumDate(max_date)
            self.max_published_date_edit.setMaximumDate(max_date)
            if prev_min_created > max_date:
                prev_min_created = max_date
            if prev_max_created > max_date:
                prev_max_created = max_date

        self.set_published_range(prev_min_created, prev_max_created)

    def clear(self):
        self.updated_date_slider.setRange(
            self.updated_date_slider.minimum(),
            self.updated_date_slider.maximum()
        )
        self.published_date_slider.setRange(
            self.published_date_slider.minimum(),
            self.published_date_slider.maximum()
        )
        self._update_labels()

    def should_show_clear(self):
        if self.published_date_slider.lowerValue() == self.published_date_slider.minimum() and \
                self.published_date_slider.upperValue() == \
                self.published_date_slider.maximum() and \
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
        self._block_changes += 1
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
        self._block_changes -= 1
