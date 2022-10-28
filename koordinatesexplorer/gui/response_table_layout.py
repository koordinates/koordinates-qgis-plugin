from typing import Optional

from qgis.PyQt.QtCore import (
    Qt,
    QRect,
    QSize
)
from qgis.PyQt.QtWidgets import (
    QLayout,
    QSizePolicy,
    QStyle,
    QWidget,
    QWidgetItem
)

from .dataset_browser_items import (
    EmptyDatasetItemWidget,
    DatasetItemWidget
)


class ResponsiveTableLayout(QLayout):

    def __init__(self, parent, hspacing, vspacing):
        super().__init__(parent)

        self.hspacing = hspacing
        self.vspacing = vspacing

        self._column_count = 1

        self.itemList = []

    def __del__(self):
        item = self.takeAt(0)
        while item:
            item = self.takeAt(0)

    def addItem(self, item):
        self.itemList.append(item)

    def insert_widget(self, idx, widget):
        self.addChildWidget(widget)
        item = QWidgetItem(widget)
        self.itemList.insert(idx, item)
        self.invalidate()

    def horizontalSpacing(self):
        if self.hspacing >= 0:
            return self.hspacing
        return self.smartSpacing(QStyle.PM_LayoutHorizontalSpacing)

    def verticalSpacing(self):
        if self.vspacing >= 0:
            return self.vspacing
        return self.smartSpacing(QStyle.PM_LayoutVerticalSpacing)

    def count(self):
        return len(self.itemList)

    def itemAt(self, index):
        if 0 <= index < len(self.itemList):
            return self.itemList[index]

        return None

    def takeAt(self, index):
        if 0 <= index < len(self.itemList):
            return self.itemList.pop(index)

        return None

    def expandingDirections(self):
        return Qt.Orientations()  # Qt.Orientation.Horizontal)

    def hasHeightForWidth(self):
        return True

    def heightForWidth(self, width):
        height = self._doLayout(QRect(0, 0, width, 0), True)
        return height

    def setGeometry(self, rect):
        super().setGeometry(rect)
        self._doLayout(rect, False)

    def sizeHint(self):
        return self.minimumSize()

    def column_count(self):
        return self._column_count

    def minimumSize(self):
        size = QSize()

        for item in self.itemList:
            size = size.expandedTo(item.minimumSize())

        margins = self.contentsMargins()
        size += QSize(margins.left() + margins.right(),
                      margins.top() + margins.bottom())
        return size

    def _doLayout(self, rect, testOnly):
        margins = self.contentsMargins()
        left = margins.left()
        top = margins.top()
        right = margins.right()
        bottom = margins.bottom()

        effective_rect = rect.adjusted(left, top, -right, -bottom)

        if effective_rect.width() < 500:
            col_count = 1
        else:
            col_count = int(effective_rect.width() / 270)

        col_count = max(1, col_count)

        space_x = self.horizontalSpacing()
        space_y = self.verticalSpacing()

        width_without_spacing = effective_rect.width() - (col_count - 1) * space_x
        col_width = int(width_without_spacing / col_count)

        x = effective_rect.x()
        y = effective_rect.y()
        line_height = 0

        y_offsets = [y]

        assigned_lines = []
        current_line_items = []

        visible_items = [i for i in self.itemList if i.widget().isVisible()]

        if not visible_items:
            return 0

        for item in visible_items:
            next_x = x + col_width + space_x

            current_line_items.append(item)
            line_height = max(line_height, item.sizeHint().height())
            if len(current_line_items) == col_count:
                assigned_lines.append(current_line_items[:])
                current_line_items = []

                x = effective_rect.x()
                y = y + line_height + space_y
                y_offsets.append(y)

                next_x = x + item.minimumSize().width() + space_x
                line_height = 0

            x = next_x

        if current_line_items:
            assigned_lines.append(current_line_items[:])

        if not testOnly:
            self._column_count = col_count
            for idx, line in enumerate(assigned_lines):
                y_offset = y_offsets[idx]

                x = effective_rect.left()
                for item in line:
                    item.setGeometry(
                        QRect(x, y_offset, col_width, item.sizeHint().height())
                    )

                    try:
                        item.widget().set_column_count(col_count)
                    except AttributeError:
                        pass

                    x += col_width + space_x

        return y + line_height - rect.y() + bottom

    def smartSpacing(self, pm):
        parent = self.parent()
        if not parent:
            return -1
        elif parent.isWidgetType():
            return parent.style().pixelMetric(pm, None, parent)
        else:
            return parent.spacing()


class ResponsiveTableWidget(QWidget):
    VERTICAL_SPACING = 10
    HORIZONTAL_SPACING = 10

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        self.setLayout(ResponsiveTableLayout(parent=None, vspacing=self.VERTICAL_SPACING,
                                             hspacing=self.HORIZONTAL_SPACING))

        self.layout().setContentsMargins(0, 0, 16, 16)

        self._widgets = []

    def clear(self):
        for w in self._widgets:
            w.deleteLater()
            self.layout().takeAt(0)
        self._widgets = []

    def column_count(self):
        return self.layout().column_count()

    def push_empty_widget(self):
        empty_widget = EmptyDatasetItemWidget()
        self.push_widget(empty_widget)

    def find_next_empty_widget(self) -> Optional[QWidget]:

        for w in self._widgets:
            if isinstance(w, EmptyDatasetItemWidget):
                return w

        return None

    def replace_widget(self, old_widget, new_widget):
        idx = self._widgets.index(old_widget)
        self._widgets[idx].setParent(None)
        self._widgets[idx].deleteLater()

        self._widgets[idx] = new_widget
        self._widgets[idx].setParent(self)

        self.layout().insert_widget(idx, new_widget)

        self.layout().takeAt(idx + 1)

    def push_dataset(self, dataset):
        dataset_widget = DatasetItemWidget(dataset, self.column_count(), self)

        next_empty_widget = self.find_next_empty_widget()
        if next_empty_widget is not None:
            self.replace_widget(next_empty_widget, dataset_widget)
        else:
            self.push_widget(dataset_widget)

    def push_widget(self, widget):
        self._widgets.append(widget)
        self.layout().addWidget(widget)

    def remove_empty_widgets(self):
        for idx in range(len(self._widgets) - 1, -1, -1):
            if isinstance(self._widgets[idx], EmptyDatasetItemWidget):
                self._widgets[idx].setParent(None)
                self._widgets[idx].deleteLater()
                self.layout().takeAt(idx)
                del self._widgets[idx]

    def remove_widget(self, widget):
        idx = self._widgets.index(widget)
        self._widgets[idx].setParent(None)
        self._widgets[idx].deleteLater()
        self.layout().takeAt(idx)
        del self._widgets[idx]
