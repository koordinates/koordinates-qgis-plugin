from qgis.PyQt.QtCore import (
    Qt,
    QSize
)
from qgis.PyQt.QtGui import (
    QPixmap,
    QImage
)
from qgis.PyQt.QtWidgets import (
    QLabel
)

from koordinates.gui.thumbnails import downloadThumbnail


class ThumbnailLabel(QLabel):
    """
    A fixed size label showing a deferred loaded thumbnail image
    """

    def __init__(self, url: str, width, height, parent=None):
        super().__init__(parent)
        self.setFixedSize(QSize(width, height))

        downloadThumbnail(url, self)

    def setThumbnail(self, image: QImage):
        image = image.convertToFormat(QImage.Format_ARGB32)
        if image.width() > self.width():
            image = image.scaled(
                self.width(),
                int(image.height() * self.width() / image.width()),
                transformMode=Qt.SmoothTransformation
            )
            self.setFixedHeight(image.height())

        if image.height() > self.height():
            image = image.scaled(
                int(image.width() * self.height() / image.height()),
                self.height(),
                transformMode=Qt.SmoothTransformation)
            self.setFixedWidth(image.width())

        self.setPixmap(QPixmap.fromImage(image))
