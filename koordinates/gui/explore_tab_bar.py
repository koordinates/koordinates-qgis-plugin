from typing import (
    Optional,
    List
)

from qgis.PyQt import sip
from qgis.PyQt.QtCore import (
    Qt,
    QSize,
    pyqtSignal
)
from qgis.PyQt.QtGui import (
    QPainter,
    QBrush,
    QColor,
    QPen,
    QPainterPath,
    QFontMetrics
)
from qgis.PyQt.QtWidgets import (
    QWidget,
    QTabBar,
    QStyle,
    QStylePainter,
    QStyleOptionTab,
    QStyleOptionButton,
    QPushButton
)

from .enums import (
    TabStyle,
    StandardExploreModes
)
from .gui_utils import GuiUtils
from ..api import (
    KoordinatesClient,
    ExploreSection
)


class FlatTabBar(QTabBar):
    """
    A flat (material you) style tab bar widget
    """

    CORNER_RADIUS = 4

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setIconSize(QSize(24, 24))
        self.setExpanding(False)

    def bottom_tab_style(self, index: int) -> TabStyle:
        """
        Returns the bottom tab style for the tab at the given index

        The default implementation always uses rounded tab bottoms
        """
        return TabStyle.Rounded

    def paintEvent(self, event):
        painter = QStylePainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)

        for i in range(self.count()):
            option = QStyleOptionTab()
            self.initStyleOption(option, i)

            _bottom_tab_style = self.bottom_tab_style(i)

            if option.state & QStyle.State_Selected:
                painter.save()
                brush = QBrush(QColor(219, 219, 219))
                painter.setBrush(brush)
                painter.setPen(Qt.NoPen)
                if _bottom_tab_style == TabStyle.Rounded:
                    painter.drawRoundedRect(option.rect,
                                            self.CORNER_RADIUS,
                                            self.CORNER_RADIUS)
                else:
                    path = QPainterPath()
                    path.moveTo(option.rect.left() + self.CORNER_RADIUS,
                                option.rect.top())
                    path.lineTo(option.rect.right() - self.CORNER_RADIUS,
                                option.rect.top())
                    path.arcTo(option.rect.right() - self.CORNER_RADIUS * 2,
                               option.rect.top(),
                               self.CORNER_RADIUS * 2,
                               self.CORNER_RADIUS * 2,
                               90, -90
                               )
                    path.lineTo(option.rect.right(),
                                option.rect.bottom() + 1)
                    path.lineTo(option.rect.left(),
                                option.rect.bottom() + 1)
                    path.lineTo(option.rect.left(),
                                option.rect.top() + self.CORNER_RADIUS)
                    path.arcTo(option.rect.left(),
                               option.rect.top(),
                               self.CORNER_RADIUS * 2,
                               self.CORNER_RADIUS * 2,
                               180, -90
                               )
                    painter.drawPath(path)
                painter.restore()

            option.state = option.state & (~QStyle.State_Selected)
            painter.drawControl(QStyle.CE_TabBarTabLabel, option)


class FlatUnderlineTabBar(QTabBar):
    """
    A flat (material you) style tab bar widget, which underlines the selected tab
    """

    LINE_WIDTH = 4
    HORIZONTAL_SPACING = 24
    LEFT_MARGIN = 8

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setIconSize(QSize(24, 24))
        self.setExpanding(False)
        font = self.font()
        font.setBold(True)
        self.setFont(font)
        self._tab_color = QColor('#0a9b46')

    def sizeHint(self):
        return QSize(0, 36)

    def tabSizeHint(self, index: int):
        text = self.tabText(index)
        fm = QFontMetrics(self.font())
        text_width = int(fm.boundingRect(text).width() * 1.03)
        margin = self.LEFT_MARGIN if index == 0 else 0
        return QSize(margin + text_width + self.HORIZONTAL_SPACING,
                     self.sizeHint().height())

    def paintEvent(self, event):
        painter = QStylePainter(self)

        painter.setRenderHint(QPainter.Antialiasing, True)

        for i in range(self.count()):
            option = QStyleOptionTab()
            self.initStyleOption(option, i)
            if i == 0:
                option.rect.setLeft(option.rect.left() + self.LEFT_MARGIN)

            option.rect.setWidth(option.rect.width() - self.HORIZONTAL_SPACING)

            if option.state & QStyle.State_Selected:
                painter.save()
                painter.setRenderHint(QPainter.Antialiasing, False)
                painter.setBrush(Qt.NoBrush)
                pen = QPen(self._tab_color)
                pen.setWidth(self.LINE_WIDTH)
                painter.setPen(pen)
                painter.drawLine(option.rect.left(),
                                 self.rect().bottom(),
                                 option.rect.right(),
                                 self.rect().bottom())
                painter.restore()

            option.state = option.state & (~QStyle.State_Selected)
            painter.setFont(self.font())
            painter.drawText(option.rect,
                             Qt.TextDontClip | Qt.AlignLeft | Qt.AlignVCenter,
                             option.text)


class ExploreTabBar(FlatTabBar):
    """
    Custom tab bar widget for explore actions
    """

    mode_changed = pyqtSignal()

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)

        self.addTab(GuiUtils.get_icon('browse.svg'), self.tr('Browse'))
        self.setTabData(0, StandardExploreModes.Browse)
        self.addTab(GuiUtils.get_icon('publishers.svg'), self.tr('Publishers'))
        self.setTabData(1, StandardExploreModes.Publishers)

        KoordinatesClient.instance().explore_sections_retrieved.connect(
            self._explore_sections_retrieved
        )

        self.currentChanged.connect(self._tab_changed)

    def _tab_changed(self, index):
        """
        Called when the tab is changed
        """
        self.mode_changed.emit()

    def bottom_tab_style(self, index: int) -> TabStyle:
        current_mode: str = self.tabData(index)
        return {
            StandardExploreModes.Browse: TabStyle.Flat,
            StandardExploreModes.Publishers: TabStyle.Flat
        }.get(current_mode, TabStyle.Rounded)

    def current_mode(self) -> str:
        """
        Returns the current explore mode
        """
        return self.tabData(self.currentIndex())

    def set_mode(self, mode: str):
        """
        Sets the current explore mode
        """
        for i in range(self.count()):
            if self.tabData(i) == mode:
                self.setCurrentIndex(i)

    def _explore_sections_retrieved(self, sections: List[ExploreSection]):
        if sip.isdeleted(self):
            return

        for section in sections:
            if section.slug == 'popular':
                # special case for popular, should always be first tab
                self.insertTab(
                    0,
                    section.icon or GuiUtils.get_icon('popular.svg'),
                    section.label
                )
                self.setTabToolTip(0, section.description)
                self.setTabData(0, StandardExploreModes.Popular)
            else:
                self.addTab(
                    section.icon or GuiUtils.get_icon('popular.svg'),
                    section.label
                )
                tab_index = self.count() - 1
                self.setTabToolTip(tab_index, section.description)
                self.setTabData(tab_index, section.slug)


class ExploreTabButton(QPushButton):
    """
    Custom button for displaying tab style switcher as vertical stack
    """
    CORNER_RADIUS = 4

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setCheckable(True)
        self.setIconSize(QSize(24, 24))
        self.setStyleSheet("text-align:left;")

        self.bottom_tab_style = TabStyle.Rounded

    def sizeHint(self):
        hint = super().sizeHint()
        hint.setHeight(int(hint.height() * 1.25))
        return hint

    def paintEvent(self, event):
        painter = QStylePainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)

        option = QStyleOptionButton()
        self.initStyleOption(option)

        if option.state & QStyle.State_On:
            painter.save()
            brush = QBrush(QColor(219, 219, 219))
            painter.setBrush(brush)
            painter.setPen(Qt.NoPen)
            if self.bottom_tab_style == TabStyle.Rounded:
                painter.drawRoundedRect(option.rect,
                                        self.CORNER_RADIUS,
                                        self.CORNER_RADIUS)
            else:
                path = QPainterPath()
                path.moveTo(option.rect.left() + self.CORNER_RADIUS,
                            option.rect.top())
                path.lineTo(option.rect.right() - self.CORNER_RADIUS,
                            option.rect.top())
                path.arcTo(option.rect.right() - self.CORNER_RADIUS * 2,
                           option.rect.top(),
                           self.CORNER_RADIUS * 2,
                           self.CORNER_RADIUS * 2,
                           90, -90
                           )
                path.lineTo(option.rect.right(),
                            option.rect.bottom() + 1)
                path.lineTo(option.rect.left(),
                            option.rect.bottom() + 1)
                path.lineTo(option.rect.left(),
                            option.rect.top() + self.CORNER_RADIUS)
                path.arcTo(option.rect.left(),
                           option.rect.top(),
                           self.CORNER_RADIUS * 2,
                           self.CORNER_RADIUS * 2,
                           180, -90
                           )
                painter.drawPath(path)
            painter.restore()

        option.state = option.state & (~QStyle.State_Selected)
        option.rect.translate(12, 0)
        painter.drawControl(QStyle.CE_PushButtonLabel, option)
