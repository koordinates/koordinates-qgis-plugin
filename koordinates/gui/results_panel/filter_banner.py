import platform
from typing import Optional

from qgis.PyQt.QtCore import (
    pyqtSignal,
    Qt,
    QSize,
    QPointF,
    QRectF
)
from qgis.PyQt.QtGui import (
    QColor,
    QImage,
    QFontMetrics,
    QPainter,
    QPen,
    QBrush
)
from qgis.PyQt.QtWidgets import (
    QWidget,
    QStyleOption,
    QStylePainter,
    QSizePolicy
)

from ..gui_utils import GuiUtils
from ..thumbnails import (
    downloadThumbnail,
    PublisherThumbnailProcessor
)
from ...api import (
    Publisher,
    PublisherType
)


class FilterBannerWidget(QWidget):
    """
    Shows a filter as a banner widget
    """
    THUMBNAIL_CORNER_RADIUS = 7
    VERTICAL_MARGIN = 7
    HORIZONTAL_MARGIN = 5
    THUMBNAIL_WIDTH = 118
    THUMBNAIL_MARGIN = 3
    MARGIN_LEFT = 10

    closed = pyqtSignal()

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self._icon: Optional[QImage] = None
        self._background: Optional[QColor] = None
        self._foreground: Optional[QColor] = None
        self.setMouseTracking(True)
        self.setSizePolicy(
            QSizePolicy.Preferred,
            QSizePolicy.Fixed
        )

    def set_icon(self, icon: QImage):
        """
        Sets the icon image for the banner
        """
        self._icon = icon
        self.update()

    def set_background_color(self, color: QColor):
        """
        Sets the background color for the banner
        """
        self._background = color
        self.update()

    def set_foreground_color(self, color: QColor):
        """
        Sets the foreground color for the banner
        """
        self._foreground = color
        self.update()

    def setThumbnail(self, image: QImage):
        self.set_icon(image)

    def sizeHint(self):
        return QSize(1000, int(QFontMetrics(self.font()).height() * 3))

    def close_button_rect(self):
        return QRectF(self.width() - 16 - self.HORIZONTAL_MARGIN,
                      0,
                      16, self.height())

    def mouseMoveEvent(self, event):
        if self.close_button_rect().contains(event.pos()):
            self.setCursor(Qt.PointingHandCursor)
        else:
            self.setCursor(Qt.ArrowCursor)

    def mousePressEvent(self, event):
        if self.close_button_rect().contains(event.pos()):
            self.closed.emit()

    def paintEvent(self, event):
        option = QStyleOption()
        option.initFrom(self)

        painter = QStylePainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)

        painter.setPen(Qt.NoPen)
        if self._foreground:
            painter.setBrush(QBrush(self._foreground))
        else:
            painter.setBrush(QBrush(QColor(255, 255, 255)))

        rect = QRectF(option.rect)
        inner_rect = rect
        inner_rect.adjust(self.HORIZONTAL_MARGIN,
                          self.VERTICAL_MARGIN,
                          -self.HORIZONTAL_MARGIN,
                          -self.VERTICAL_MARGIN)
        painter.drawRoundedRect(inner_rect,
                                self.THUMBNAIL_CORNER_RADIUS,
                                self.THUMBNAIL_CORNER_RADIUS)

        thumbnail_rect = inner_rect
        thumbnail_rect.setWidth(self.THUMBNAIL_WIDTH)

        background_color = self._background
        if not background_color:
            background_color = QColor('#f5f5f7')

        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(background_color))
        painter.drawRoundedRect(option.rect,
                                self.THUMBNAIL_CORNER_RADIUS,
                                self.THUMBNAIL_CORNER_RADIUS)

        if self._icon and not self._icon.isNull():
            scaled = self._icon.scaled(
                QSize(
                    int(thumbnail_rect.width()) - 2 * self.THUMBNAIL_MARGIN,
                    int(option.rect.height()) - 2 * self.THUMBNAIL_MARGIN),
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation)

            center_y = int((thumbnail_rect.height() - scaled.height()) / 2)
            painter.drawImage(QRectF(option.rect.left() + self.MARGIN_LEFT,
                                     thumbnail_rect.top() + center_y,
                                     scaled.width(), scaled.height()),
                              scaled)

        painter = None

        self._draw_content(event)

        painter = QStylePainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)

        if background_color.lightnessF() < 0.5:
            image = GuiUtils.get_svg_as_image('close-reversed.svg', 16, 16)
        else:
            image = GuiUtils.get_svg_as_image('close.svg', 16, 16)

        center_y = (self.height() - image.height()) / 2
        painter.drawImage(QRectF(
            option.rect.right() - image.width() - self.HORIZONTAL_MARGIN,
            option.rect.top() + center_y,
            image.width(), image.height()),
                          image)


class PublisherFilterBannerWidget(FilterBannerWidget):
    """
    Shows a publisher filter as a banner widget
    """

    TEXT_LEFT_EDGE_PUBLISHER = 130
    TEXT_LEFT_EDGE_USER = 70
    TEXT_LEFT_EDGE_MIRROR = 20

    def __init__(self, publisher: Publisher, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.publisher = publisher

        if self.publisher.publisher_type == PublisherType.Publisher:
            self.set_foreground_color(QColor(255, 255, 255))
            if self.publisher.theme.background_color():
                self.set_background_color(self.publisher.theme.background_color())
            else:
                self.set_background_color(
                    QColor('#555657'))
        elif self.publisher.publisher_type == PublisherType.Mirror:
            self.set_foreground_color(QColor(255, 255, 255))
            self.set_background_color(QColor('#555658'))
        elif self.publisher.publisher_type == PublisherType.User:
            self.set_foreground_color(QColor(0, 0, 0))
            self.set_background_color(QColor(255, 255, 255))

        if self.publisher.publisher_type != PublisherType.Mirror:
            thumbnail_processor = PublisherThumbnailProcessor(
                self.publisher,
                QSize(self.THUMBNAIL_WIDTH, self.height())
            )
            if self.publisher.theme.logo():
                downloadThumbnail(self.publisher.theme.logo(),
                                  self,
                                  thumbnail_processor
                                  )
            else:
                self.set_icon(thumbnail_processor.default_thumbnail())

    def _draw_content(self, event):
        option = QStyleOption()
        option.initFrom(self)

        painter = QStylePainter(self)

        if self.publisher.publisher_type == PublisherType.Publisher:
            heading_font_size = 10
            if platform.system() == 'Darwin':
                heading_font_size = 12
        else:
            heading_font_size = 12
            if platform.system() == 'Darwin':
                heading_font_size = 14

        font = self.font()
        metrics = QFontMetrics(font)
        font.setPointSizeF(heading_font_size)
        font.setBold(True)
        painter.setFont(font)

        if self.publisher.publisher_type == PublisherType.Publisher:
            line_heights = [1.2, 2.1]
            left_text_edge = option.rect.left() + self.TEXT_LEFT_EDGE_PUBLISHER
        elif self.publisher.publisher_type == PublisherType.Mirror:
            line_heights = [1.7, 0]
            left_text_edge = option.rect.left() + self.TEXT_LEFT_EDGE_MIRROR
        else:
            line_heights = [1.6, 0]
            left_text_edge = option.rect.left() + self.TEXT_LEFT_EDGE_USER

        painter.setBrush(Qt.NoBrush)
        if self._foreground:
            painter.setPen(QPen(self._foreground))
        else:
            painter.setPen(QPen(QColor(255, 255, 255)))

        max_line_width = metrics.boundingRect(self.publisher.name()).width()
        painter.drawText(QPointF(left_text_edge,
                                 option.rect.top() + int(
                                     metrics.height() * line_heights[0])),
                         self.publisher.name())

        font.setBold(False)
        painter.setFont(font)

        if line_heights[1]:
            painter.drawText(QPointF(left_text_edge,
                                     option.rect.top() + int(
                                         metrics.height() * line_heights[1])),
                             'via ' + self.publisher.site.name())

        if self.publisher.publisher_type == PublisherType.Mirror:
            mirror_image = GuiUtils.get_svg_as_image(
                'mirror_white.svg', 50, 16
            )
            center_y = int((option.rect.height() - mirror_image.height()) / 2)
            painter.drawImage(QRectF(
                option.rect.left() + max_line_width + 50,
                option.rect.top() + center_y,
                mirror_image.width(),
                mirror_image.height()),
                mirror_image)
