from typing import List, Dict

from qgis.PyQt import sip
from qgis.PyQt.QtCore import (
    Qt,
    QSize,
    pyqtSignal
)
from qgis.PyQt.QtGui import (
    QPalette,
    QPixmap,
    QImage,
    QPainter,
    QCursor,
    QColor
)
from qgis.PyQt.QtSvg import QSvgWidget
from qgis.PyQt.QtWidgets import (
    QWidget,
    QLabel,
    QStyle,
    QStyleOptionFrame,
    QFrame,
    QVBoxLayout,
    QApplication,
    QSizePolicy,
    QToolButton,
    QHBoxLayout,
    QWidgetAction,
)
from qgis.gui import (
    QgsFloatingWidget
)

from .gui_utils import GuiUtils
from .thumbnails import downloadThumbnail


class ContextIcon(QLabel):
    SIZE = 30
    CORNER_RADIUS = 3

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(QSize(ContextIcon.SIZE, ContextIcon.SIZE))

    def setThumbnail(self, image: QImage):
        image = image.convertToFormat(QImage.Format_ARGB32)
        if image.width() != ContextIcon.SIZE or image.height() != ContextIcon.SIZE:
            image = image.scaled(ContextIcon.SIZE, ContextIcon.SIZE,
                                 transformMode=Qt.SmoothTransformation)

        # round corners of image
        rounded_image = QImage(ContextIcon.SIZE, ContextIcon.SIZE, QImage.Format_ARGB32)
        rounded_image.fill(Qt.transparent)
        painter = QPainter(rounded_image)
        painter.setRenderHint(QPainter.Antialiasing, True)
        painter.setPen(Qt.NoPen)
        painter.setBrush(Qt.black)
        painter.drawRoundedRect(0, 0, ContextIcon.SIZE, ContextIcon.SIZE,
                                ContextIcon.CORNER_RADIUS, ContextIcon.CORNER_RADIUS)
        painter.setCompositionMode(QPainter.CompositionMode_SourceIn)
        painter.drawImage(0, 0, image)
        painter.end()

        self.setPixmap(QPixmap.fromImage(rounded_image))


class ContextLogo(QLabel):
    LOGO_HEIGHT = 32

    def __init__(self, parent=None):
        super().__init__(parent)

    def setThumbnail(self, image: QImage):
        if image.height() > ContextLogo.LOGO_HEIGHT:
            image = image.scaled(
                int(image.width() * ContextLogo.LOGO_HEIGHT / image.height()),
                ContextLogo.LOGO_HEIGHT,
                transformMode=Qt.SmoothTransformation
            )

        self.setPixmap(QPixmap.fromImage(image))


class ContextItem(QFrame):
    selected = pyqtSignal(str)

    def __init__(self, details: Dict):
        super().__init__()
        self._details = details
        self._selected = False

        self.setMouseTracking(True)
        self.setObjectName('context_item')
        self.setCursor(QCursor(Qt.PointingHandCursor))

        self.setFrameShape(QFrame.NoFrame)

        hl = QHBoxLayout()
        self.icon_label = ContextIcon()

        if self._details['name'] == 'All data':
            self.icon_label.setThumbnail(
                GuiUtils.get_svg_as_image(
                    'kx_icon.svg',
                    ContextIcon.SIZE,
                    ContextIcon.SIZE,
                    QColor(0, 0, 0)
                ))
        elif self._details.get('org') and self._details['org'].get('logo_square_url'):
            downloadThumbnail(self._details["org"]["logo_square_url"], self.icon_label)
        elif self._details.get('logo'):
            downloadThumbnail(self._details["logo"], self.icon_label)

        hl.addWidget(self.icon_label)
        self.name_label = QLabel(self._details['name'])
        hl.addWidget(self.name_label, 1)
        self.checked_label = QSvgWidget()
        self.checked_label.setFixedSize(16, 16)
        hl.addWidget(self.checked_label)

        self.set_selected(False)

        self.setLayout(hl)

    def context_name(self) -> str:
        return self._details['name']

    def set_selected(self, selected):
        self._selected = selected
        back_color = '#ffffff'
        if self._selected:
            back_color = '#f5f5f7'
            self.checked_label.load(
                GuiUtils.get_icon_svg(
                    'tick.svg'
                )
            )
        else:
            self.checked_label.load(None)

        self.setStyleSheet(
            """
            #context_item {{ background-color: {}; border: 1px solid #dddddd; border-radius: 4px }}
            #context_item:hover {{ background-color: #f5f5f7; }}
            """.format(back_color))

        self.update()

    def mouseReleaseEvent(self, event):
        if event.button() != Qt.LeftButton:
            return

        self.selected.emit(self._details['name'])


class ContextItemMenuAction(QWidgetAction):
    selected = pyqtSignal(str)

    def __init__(self, details: Dict, selected: bool, is_first_action = False, parent=None):
        super().__init__(parent)

        self.widget = ContextItem(details)
        self.widget.set_selected(selected)
        self.widget.selected.connect(self.selected)

        padding_widget = QWidget()
        hl = QHBoxLayout()
        if is_first_action:
            hl.setContentsMargins(8,8,8, 8)
        else:
            hl.setContentsMargins(8, 0, 8, 8)
        hl.addWidget(self.widget)
        padding_widget.setLayout(hl)

        self.setDefaultWidget(padding_widget)




class ContextWidget(QWidget):
    """
    A custom widget for selection of context
    """

    context_changed = pyqtSignal(dict)

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
            # self.frame.setFixedWidth(self.anchorWidget().size().width())
            self.frame.updateGeometry()
            self.frame.adjustSize()
            self.updateGeometry()
            self.adjustSize()

        def showEvent(self, e):
            super().showEvent(e)
            if not e.spontaneous():
                self.ensurePolished()
                self.reflow()

    def __init__(self, parent):
        super().__init__(parent)

        self._contexts = []
        self._reset_contexts()
        self._current_context_name: str = 'All data'

        self.setFocusPolicy(Qt.StrongFocus)

        hl = QHBoxLayout()
        hl.setContentsMargins(0, 0, 0, 0)

        self.label = ContextLogo()
        hl.addWidget(self.label)

        self.drop_down_button = QToolButton()
        self.drop_down_button.setAutoRaise(True)
        self.drop_down_button.setArrowType(Qt.DownArrow)
        self.drop_down_button.setCheckable(True)
        hl.addWidget(self.drop_down_button)

        self.setLayout(hl)

        self._floating_widget = ContextWidget.ContentsWidget(self)

        self._floating_widget.hide()

        QApplication.instance().focusChanged.connect(self._on_focus_change)

        self.drop_down_button.toggled.connect(self.expand)

        self._contents_widget = QWidget()
        self._context_widgets = []
        vl = QVBoxLayout()
        vl.setContentsMargins(4, 4, 4, 4)
        self._contents_widget.setLayout(vl)
        self._contents_widget.setFixedWidth(200)
        self._floating_widget.set_contents_widget(self._contents_widget)

        self.set_contexts([])

    def __del__(self):
        if not sip.isdeleted(self._floating_widget):
            self._floating_widget.deleteLater()

    def _reset_contexts(self):
        self._contexts = [{
            "name": "All data",
            "type": "site",
            "domain": "all",
            "org": {
                "logo_square_url": "",
                "logo_owner_url": ""
            }
        }]

    def set_contexts(self, contexts=List):
        """
        Sets the context information
        """

        # remove existing widgets
        for i in range(len(self._context_widgets)):
            layout_item = self._contents_widget.layout().takeAt(0)
            widget = layout_item.widget()
            widget.setParent(None)
            widget.deleteLater()
        self._context_widgets = []

        self._reset_contexts()
        self._contexts.extend(contexts)

        for c in self._contexts:
            w = ContextItem(c)
            self._context_widgets.append(w)
            self._contents_widget.layout().addWidget(w)
            w.selected.connect(self.on_context_selected)
            if self._current_context_name == c['name']:
                w.set_selected(True)

        self._update_logo()
        self._contents_widget.updateGeometry()
        self._contents_widget.adjustSize()
        self._floating_widget.reflow()

    def _update_logo(self):
        if self._current_context_name != 'All data':
            downloadThumbnail(self.current_context()["org"]["logo_owner_url"], self.label)
        else:
            image = GuiUtils.get_svg_as_image(
                'koordinates_logo.svg',
                110,
                ContextLogo.LOGO_HEIGHT
            )

            self.label.setPixmap(QPixmap.fromImage(image))

    def count(self):
        return len(self._contexts)

    def expand(self, show):
        if not show:
            self._floating_widget.hide()
        else:
            self._floating_widget.show()
            self._floating_widget.raise_()

        if self.parent() and self.parent().parent():
            self.parent().parent().update()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        # self._floating_widget.setFixedWidth(event.size().width())
        self._floating_widget.reflow()

    def on_context_selected(self, context_name: str):
        self.drop_down_button.setChecked(False)
        if context_name == self._current_context_name:
            return

        for w in self._context_widgets:
            w.set_selected(w.context_name() == context_name)

        self._current_context_name = context_name
        self.label.setText(self._current_context_name)
        self._update_logo()

        self.context_changed.emit(self.current_context())

    def current_context(self) -> Dict:
        """
        Returns the details of the current context
        """
        return [c for c in self._contexts if c['name'] == self._current_context_name][0]

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
            self.drop_down_button.setChecked(False)
