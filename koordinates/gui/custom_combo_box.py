import math
from enum import Enum

from qgis.PyQt import sip
from qgis.PyQt.QtCore import (
    QSize,
    QPoint,
    QRect,
    Qt
)
from qgis.PyQt.QtGui import (
    QPalette,
    QIcon,
    QPainter,
    QFontMetrics
)
from qgis.PyQt.QtWidgets import (
    QWidget,
    QStyle,
    QStyleOptionFrame,
    QFrame,
    QVBoxLayout,
    QComboBox,
    QStyleOptionComboBox,
    QApplication,
    QSizePolicy
)
from qgis.core import (
    Qgis,
    QgsApplication
)
from qgis.gui import (
    QgsFloatingWidget
)


class CustomComboBox(QWidget):
    """
    A combo box style widget which shows a custom widget in the drop down,
    and offers a "clear" action to reset the widget
    """

    class ContentsWidget(QgsFloatingWidget):

        def __init__(self, parent):
            super().__init__(parent.window() if parent else None)

            self.setAnchorWidget(parent)
            self.setAnchorPoint(QgsFloatingWidget.TopLeft)
            self.setAnchorWidgetPoint(QgsFloatingWidget.BottomLeft)

            self.frame = QFrame()
            self.frame.setObjectName('base_frame')
            self.frame.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Maximum)

            opt = QStyleOptionFrame()
            border = self.style().pixelMetric(QStyle.PM_DefaultFrameWidth, opt)

            palette = QPalette()

            self.frame.setStyleSheet(
                "#base_frame {{background-color: {}; border: {}px solid {};}}".format(
                    palette.color(QPalette.Base).name(),
                    border,
                    palette.color(QPalette.Dark).name()))
            self.frame.setFrameStyle(QFrame.Panel | QFrame.Plain)

            frame_layout = QVBoxLayout()
            self.frame.setLayout(frame_layout)

            vl = QVBoxLayout()
            vl.setContentsMargins(0, 0, 0, 0)
            vl.addWidget(self.frame)

            self.setLayout(vl)

        def set_contents_widget(self, widget):
            self.setMinimumSize(widget.sizeHint())
            self.frame.layout().addWidget(widget)

        def reflow(self):
            if self.anchorWidget().width() > self.frame.sizeHint().width():
                self.frame.setFixedWidth(self.anchorWidget().width())
            else:
                self.frame.setFixedWidth(self.frame.sizeHint().width())

            self.frame.updateGeometry()
            self.frame.adjustSize()
            self.updateGeometry()
            self.adjustSize()

        def showEvent(self, e):
            super().showEvent(e)
            if not e.spontaneous():
                self.ensurePolished()
                self.reflow()

    class BoxComponent(Enum):
        DropDownButton = 1
        ClearButton = 2

    def __init__(self, parent):
        super().__init__(parent)

        self.setMouseTracking(True)
        self.setFocusPolicy(Qt.StrongFocus)

        self._clear_icon = QIcon()

        self._icon_size = math.floor(
            max(Qgis.UI_SCALE_FACTOR * self.fontMetrics().height() * 0.75, 16.0))

        self._clear_pixmap = QgsApplication.getThemeIcon("/mIconClearText.svg").pixmap(
            QSize(self._icon_size, self._icon_size))
        self._clear_hover_pixmap = QgsApplication.getThemeIcon("/mIconClearTextHover.svg").pixmap(
            QSize(self._icon_size, self._icon_size))

        self._show_clear_button = True
        self._clear_action = None

        self._current_text = ''
        self._hover_state = None

        self._floating_widget = CustomComboBox.ContentsWidget(self)

        cb = QComboBox()
        self.setMinimumHeight(cb.sizeHint().height())

        self._floating_widget.hide()

        QApplication.instance().focusChanged.connect(self._on_focus_change)

    def __del__(self):
        if not sip.isdeleted(self._floating_widget):
            self._floating_widget.deleteLater()

    def component_for_pos(self, pos: QPoint):
        """
        Returns the component for the given widget pos
        """
        option = QStyleOptionComboBox()
        option.initFrom(self)
        drop_down_rect = self.style().subControlRect(
            QStyle.CC_ComboBox, option, QStyle.SC_ComboBoxArrow, None)
        if drop_down_rect.contains(pos):
            return CustomComboBox.BoxComponent.DropDownButton

        if self.should_show_clear():
            icon_left = drop_down_rect.left() - int(drop_down_rect.width() * 1.1)
            clear_rect = QRect(icon_left, 0, self._icon_size, drop_down_rect.height())

            if clear_rect.contains(pos):
                return CustomComboBox.BoxComponent.ClearButton

        return None

    def set_contents_widget(self, widget):
        self._floating_widget.set_contents_widget(widget)

    def set_show_clear_button(self, show: bool):
        self._show_clear_button = show
        self.update()

    def should_show_clear(self):
        if not self.isEnabled() or not self._show_clear_button:
            return False

        return True

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._floating_widget.reflow()

    def mouseMoveEvent(self, event):
        self._hover_state = self.component_for_pos(event.pos())
        super().mouseMoveEvent(event)
        self.update()

    def leaveEvent(self, event):
        self._hover_state = None
        super().leaveEvent(event)
        self.update()

    def _on_focus_change(self, old, new):
        if not self._floating_widget.isVisible():
            return

        parent = new
        while parent:
            if parent == self._floating_widget:
                break
            else:
                try:
                    parent = parent.parent()
                except:  # noqa: E722
                    parent = None

        if not parent and new != self:
            self._floating_widget.hide()
            self.parent().update()

    def mousePressEvent(self, event):
        component = self.component_for_pos(event.pos())
        if component == CustomComboBox.BoxComponent.DropDownButton:
            self._show_drop_down()
        elif component == CustomComboBox.BoxComponent.ClearButton:
            self.clear()
        else:
            pass

        super().mouseMoveEvent(event)
        self.update()

    def clear(self):
        pass

    def _show_drop_down(self):
        if self._floating_widget.isVisible():
            self._floating_widget.hide()
        else:
            self._floating_widget.show()
            self._floating_widget.raise_()

        if self.parent() and self.parent().parent():
            self.parent().parent().update()

    def is_expanded(self):
        return self._floating_widget.isVisible()

    def collapse(self):
        if self._floating_widget.isVisible():
            self._floating_widget.hide()

        if self.parent() and self.parent().parent():
            self.parent().update()
            self.parent().parent().update()

    def expand(self):
        if not self._floating_widget.isVisible():
            self._show_drop_down()

        if self.parent() and self.parent().parent():
            self.parent().parent().update()

    def set_current_text(self, text):
        self._current_text = text
        self.update()

    def paintEvent(self, event):
        super().paintEvent(event)

        painter = QPainter(self)

        option = QStyleOptionComboBox()
        option.initFrom(self)
        option.rect = event.rect()
        available_space = option.rect.width() - 60

        fm = QFontMetrics(self.font())
        text = self._current_text
        while len(text) > 5 and fm.width(text) > available_space:
            text = text[:-1]

        if text != self._current_text:
            text += "…"

        option.currentText = text
        option.editable = True

        if self._hover_state == CustomComboBox.BoxComponent.DropDownButton:
            option.state |= QStyle.State_MouseOver
        else:
            option.state &= ~QStyle.State_MouseOver

        style = self.style()

        self.style().drawComplexControl(QStyle.CC_ComboBox, option, painter, None)
        option.editable = False
        style.drawControl(QStyle.CE_ComboBoxLabel, option, painter, None)

        show_clear = self.should_show_clear()
        if show_clear:
            drop_down_rect = style.subControlRect(
                QStyle.CC_ComboBox, option,
                QStyle.SC_ComboBoxArrow, None)
            icon_left = drop_down_rect.left() - int(drop_down_rect.width() * 1.1)
            icon_top = drop_down_rect.top() + int(
                (drop_down_rect.height() - self._icon_size) * 0.5)
            pixmap = self._clear_pixmap \
                if self._hover_state != CustomComboBox.BoxComponent.ClearButton \
                else self._clear_hover_pixmap
            painter.drawPixmap(icon_left, icon_top, pixmap)

        painter.end()
