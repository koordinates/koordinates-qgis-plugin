import math

from qgis.PyQt.QtCore import (
    Qt,
    QRect,
    QSize
)
from qgis.PyQt.QtWidgets import (
    QLayout,
    QSizePolicy,
    QStyle
)


class FlowLayout(QLayout):
    def __init__(self, parent=None, margin=-1, hspacing=-1, vspacing=-1):
        super().__init__(parent)

        self.hspacing = hspacing
        self.vspacing = vspacing
        self.setContentsMargins(margin, margin, margin, margin)

        self.itemList = []

    def __del__(self):
        item = self.takeAt(0)
        while item:
            item = self.takeAt(0)

    def addItem(self, item):
        self.itemList.append(item)

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

    def minimumSize(self):
        size = QSize()

        for item in self.itemList:
            size = size.expandedTo(item.minimumSize())

        margins = self.contentsMargins()
        size += QSize(margins.left() + margins.right(),
                      margins.top() + margins.bottom())
        return size

    def _doLayout(self, rect, testOnly):

        def max_widget_width_for_line(items, effective_rect):
            spacing = []
            for _item in items:
                _space_x = self.horizontalSpacing()
                _wid = _item.widget()
                if _space_x == -1:
                    _space_x = _wid.style().layoutSpacing(
                        QSizePolicy.PushButton,
                        QSizePolicy.PushButton,
                        Qt.Horizontal
                    )

                spacing.append(_space_x)

            total_spacing = sum(spacing[:-1])

            available_width_for_widgets = effective_rect.width() - total_spacing

            widget_width = int(available_width_for_widgets / len(items))
            return widget_width

        margins = self.contentsMargins()
        left = margins.left()
        top = margins.top()
        right = margins.right()
        bottom = margins.bottom()

        effective_rect = rect.adjusted(left, top, -right, -bottom)

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
            wid = item.widget()
            space_x = self.horizontalSpacing()
            if space_x == -1:
                space_x = wid.style().layoutSpacing(
                    QSizePolicy.PushButton,
                    QSizePolicy.PushButton,
                    Qt.Horizontal
                )
            space_y = self.verticalSpacing()
            if space_y == -1:
                space_y = wid.style().layoutSpacing(
                    QSizePolicy.PushButton,
                    QSizePolicy.PushButton,
                    Qt.Vertical
                )

            next_x = x + item.minimumSize().width() + space_x
            if next_x - space_x > effective_rect.right() and line_height > 0:
                assigned_lines.append(current_line_items[:])
                current_line_items = []

                x = effective_rect.x()
                y = y + line_height + space_y
                y_offsets.append(y)

                next_x = x + item.minimumSize().width() + space_x
                line_height = 0

            current_line_items.append(item)

            x = next_x
            line_height = max(line_height, item.sizeHint().height())

        if current_line_items:
            assigned_lines.append(current_line_items[:])

        if not testOnly:

            min_required_lines = len(assigned_lines)
            # now that we now the absolute MINIMUM number of
            # lines required for the widgets, let's evenly
            # space them out over the required rows
            # we don't want:
            # OO OO OO
            # OO
            # rather, we want
            # OOO  OOO
            # OOO  OOO
            # !

            widgets_per_line = math.ceil(len(visible_items) / min_required_lines)

            new_assigned_lines = []
            current_row = []
            for item in visible_items:
                if len(current_row) < widgets_per_line:
                    current_row.append(item)
                else:
                    new_assigned_lines.append(current_row[:])
                    current_row = [item]
            if current_row:
                new_assigned_lines.append(current_row[:])

            max_widget_width = 999999999999
            for line in new_assigned_lines:
                max_widget_width = min(max_widget_width_for_line(line, effective_rect),
                                       max_widget_width)

            for idx, line in enumerate(new_assigned_lines):
                y_offset = y_offsets[idx]

                x = effective_rect.left()
                for item in line:
                    _wid = item.widget()

                    item.setGeometry(
                        QRect(x, y_offset, max_widget_width, item.sizeHint().height())
                    )

                    space_x = self.horizontalSpacing()
                    if space_x == -1:
                        space_x = _wid.style().layoutSpacing(
                            QSizePolicy.PushButton,
                            QSizePolicy.PushButton,
                            Qt.Horizontal
                        )

                    x += max_widget_width + space_x

        return y + line_height - rect.y() + bottom

    def smartSpacing(self, pm):
        parent = self.parent()
        if not parent:
            return -1
        elif parent.isWidgetType():
            return parent.style().pixelMetric(pm, None, parent)
        else:
            return parent.spacing()
