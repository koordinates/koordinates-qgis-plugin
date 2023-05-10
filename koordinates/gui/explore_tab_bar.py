from typing import Optional

from qgis.PyQt.QtCore import (
    Qt,
    QSize
)
from qgis.PyQt.QtGui import (
    QPainter,
    QBrush,
    QColor
)
from qgis.PyQt.QtWidgets import (
    QWidget,
    QTabBar,
    QStyle,
    QStylePainter,
    QStyleOptionTab
)

from .gui_utils import GuiUtils


class FlatTabBar(QTabBar):
    """
    A flat (material you) style tab bar widget
    """

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setIconSize(QSize(24, 24))
        self.setExpanding(False)

    def paintEvent(self, event):
        painter = QStylePainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)

        for i in range(self.count()):
            option = QStyleOptionTab()
            self.initStyleOption(option, i)

            if option.state & QStyle.State_Selected:
                painter.save()
                brush = QBrush(QColor(0, 0, 0, 38))
                painter.setBrush(brush)
                painter.setPen(Qt.NoPen)
                painter.drawRoundedRect(option.rect, 4, 4)
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
        self.addTab(GuiUtils.get_icon('publishers.svg'), self.tr('Publishers'))
        self.addTab(GuiUtils.get_icon('recent.svg'), self.tr('Recent'))
