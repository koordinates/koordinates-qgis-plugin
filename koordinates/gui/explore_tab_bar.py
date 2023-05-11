from typing import (
    Optional,
    Dict
)

from qgis.PyQt.QtCore import (
    Qt,
    QSize
)
from qgis.PyQt.QtGui import (
    QPainter,
    QBrush,
    QColor,
    QPainterPath
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

from .gui_utils import GuiUtils
from .enums import TabStyle


class FlatTabBar(QTabBar):
    """
    A flat (material you) style tab bar widget
    """

    CORNER_RADIUS = 4

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setIconSize(QSize(24, 24))
        self.setExpanding(False)
        self._bottom_tab_style: Dict[int, TabStyle] = {}

    def set_bottom_tab_style(self, index: int, style: TabStyle):
        self._bottom_tab_style[index] = style
        self.update()

    def paintEvent(self, event):
        painter = QStylePainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)

        for i in range(self.count()):
            option = QStyleOptionTab()
            self.initStyleOption(option, i)

            _bottom_tab_style = self._bottom_tab_style.get(i, TabStyle.Rounded)

            if option.state & QStyle.State_Selected:
                painter.save()
                brush = QBrush(QColor(0, 0, 0, 38))
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


class ExploreTabBar(FlatTabBar):
    """
    Custom tab bar widget for explore actions
    """

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)

        self.addTab(GuiUtils.get_icon('popular.svg'), self.tr('Popular'))
        self.addTab(GuiUtils.get_icon('browse.svg'), self.tr('Browse'))
        self.set_bottom_tab_style(1, TabStyle.Flat)
        self.addTab(GuiUtils.get_icon('publishers.svg'), self.tr('Publishers'))
        self.addTab(GuiUtils.get_icon('recent.svg'), self.tr('Recent'))


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
            brush = QBrush(QColor(0, 0, 0, 38))
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
