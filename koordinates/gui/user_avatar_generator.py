from qgis.PyQt.QtCore import (
    Qt,
    QRectF,
    QPointF
)
from qgis.PyQt.QtGui import (
    QImage,
    QPainter,
    QColor,
    QBrush,
    QPen,
    QFontMetrics
)

from .gui_utils import GuiUtils


class UserAvatarGenerator:
    """
    Generates user avatar thumbnails
    """

    AVATAR_SIZE = 65
    BACK_COLOR = QColor(255, 183, 0)
    FORE_COLOR = QColor(119, 119, 119)
    AVATAR_CACHE = {}

    @classmethod
    def get_avatar(cls, name: str) -> QImage:
        """
        Returns the avatar image for the given initials
        """
        initials = UserAvatarGenerator.name_to_initials(name)
        if initials in cls.AVATAR_CACHE:
            return cls.AVATAR_CACHE[initials]

        image = UserAvatarGenerator.generate_avatar(
            initials,
            UserAvatarGenerator.FORE_COLOR,
            UserAvatarGenerator.BACK_COLOR,
            UserAvatarGenerator.AVATAR_SIZE)
        cls.AVATAR_CACHE[initials] = image
        return image

    @staticmethod
    def name_to_initials(name: str) -> str:
        """
        Extracts initials from a name
        """
        words = name.split()
        initials = [word[0].upper() for word in words]
        return ''.join(initials)[:3]

    @staticmethod
    def generate_avatar(initials: str,
                        foreground_color: QColor,
                        background_color: QColor,
                        size: int) -> QImage:
        """
        Generates an avatar image
        """
        image = QImage(size, size, QImage.Format_ARGB32_Premultiplied)
        image.fill(Qt.transparent)

        painter = QPainter(image)
        painter.setRenderHint(QPainter.Antialiasing, True)

        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(background_color))
        painter.drawEllipse(QRectF(0, 0, image.width(), image.height()))

        painter.setBrush(Qt.NoBrush)
        painter.setPen(QPen(foreground_color))
        font = GuiUtils.get_default_font()
        font.setPixelSize(int(image.height() * 0.4))
        metrics = QFontMetrics(font)

        baseline = int((image.height() + metrics.capHeight()) / 2)
        left = int(image.width() - metrics.horizontalAdvance(initials)) / 2
        painter.setFont(font)
        painter.drawText(QPointF(left, baseline),
                         initials)

        painter.end()

        return image

