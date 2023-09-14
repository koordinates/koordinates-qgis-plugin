from typing import (
    Dict,
    Optional
)
from abc import ABC, abstractmethod
from collections import defaultdict
from functools import partial

from qgis.PyQt.QtCore import (
    Qt,
    QObject,
    pyqtSignal,
    QSize
)

from qgis.PyQt.QtNetwork import QNetworkReply, QNetworkRequest
from qgis.core import QgsNetworkAccessManager
from qgis.PyQt.QtCore import QUrl
from qgis.PyQt.QtGui import (
    QImage,
    QColor,
    QPainter,
    QBrush
)

from ..api import (
    Publisher,
    PublisherType
)
from .gui_utils import GuiUtils


class ThumbnailProcessor(ABC):
    """
    An interface for processing thumbnails
    """

    @abstractmethod
    def process_thumbnail(self, thumbnail: QImage) -> QImage:
        """
        Processes the thumbnail
        """


class UserThumbnailProcessor(ThumbnailProcessor):
    """
    A thumbnail processor for user thumbnails
    """

    def __init__(self,
                 name: str,
                 size: QSize):
        self.name = name
        self.size = size

    def process_thumbnail(self, thumbnail: Optional[QImage]) -> QImage:
        from .dataset_utils import DatasetGuiUtils
        from .user_avatar_generator import UserAvatarGenerator

        if thumbnail and not thumbnail.isNull():
            scaled = DatasetGuiUtils.crop_image_to_circle(
                thumbnail, self.size.height()
            )
            return scaled

        return UserAvatarGenerator.get_avatar(
            self.name,
            self.size.height()
        )


class PublisherTypeThumbnailProcessor(ThumbnailProcessor):
    """
    A thumbnail processor for publisher type thumbnails
    """

    def __init__(self,
                 size: QSize,
                 background_color: Optional[QColor] = None):
        self.size = size
        self.background_color = background_color

    def process_thumbnail(self, thumbnail: Optional[QImage]) -> QImage:
        max_thumbnail_width = self.size.width()
        max_thumbnail_height = \
            int(min(self.size.height(),
                    thumbnail.height()))
        scaled = thumbnail.scaled(
            QSize(max_thumbnail_width, max_thumbnail_height),
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation)

        if self.background_color:
            with_background = QImage(self.size,
                                     QImage.Format_ARGB32_Premultiplied)
            with_background.fill(Qt.transparent)
            painter = QPainter(with_background)
            painter.setRenderHint(QPainter.Antialiasing, True)

            painter.setBrush(QBrush(self.background_color))
            painter.drawRoundedRect(0, 0,
                                    self.size.width(),
                                    self.size.height(),
                                    3,
                                    3)

            x_center = int((self.size.width() - scaled.width()) / 2)
            y_center = int((self.size.height() - scaled.height()) / 2)
            painter.drawImage(x_center, y_center, scaled)
            painter.end()

            scaled = with_background

        return scaled


class PublisherThumbnailProcessor(ThumbnailProcessor):
    """
    A thumbnail processor for publisher thumbnails
    """

    def __init__(self,
                 publisher: Publisher,
                 size: QSize):
        self.publisher = publisher
        self.size = size

    def default_thumbnail(self) -> QImage:
        """
        Returns the default thumbnail for the publisher
        """
        return self.process_thumbnail(None)

    def process_thumbnail(self, thumbnail: Optional[QImage]) -> QImage:
        from .dataset_utils import DatasetGuiUtils

        if self.publisher.publisher_type == PublisherType.User:
            return UserThumbnailProcessor(
                self.publisher.name(),
                self.size).process_thumbnail(thumbnail)

        if thumbnail and not thumbnail.isNull():
            if self.publisher.publisher_type == PublisherType.Publisher:
                return PublisherTypeThumbnailProcessor(
                    self.size
                ).process_thumbnail(thumbnail)
            else:
                scaled = DatasetGuiUtils.crop_image_to_circle(
                    thumbnail, thumbnail.height()
                )
            return scaled

        else:
            thumbnail = GuiUtils.get_svg_as_image('globe.svg', 40, 40)

        return thumbnail


class GenericThumbnailManager(QObject):
    """
    A generic thumbnail manager, for widgets with their own logic
    """

    downloaded = pyqtSignal(str)

    def __init__(self, parent: Optional[QObject] = None):
        super().__init__(parent)
        self.thumbnails: Dict[str, QImage] = {}
        self.queued_replies = set()

    def thumbnail(self, url: str) -> Optional[QImage]:
        return self.thumbnails.get(url)

    def download_thumbnail(self, url: str):
        if url in self.thumbnails:
            return self.thumbnails[url]
        else:
            req = QNetworkRequest(QUrl(url))
            req.setAttribute(QNetworkRequest.CacheLoadControlAttribute, QNetworkRequest.PreferCache)
            req.setAttribute(QNetworkRequest.CacheSaveControlAttribute, True)
            reply = QgsNetworkAccessManager.instance().get(req)
            self.queued_replies.add(reply)
            if reply.isFinished():
                self.thumbnail_downloaded(reply)
            else:
                reply.finished.connect(partial(self.thumbnail_downloaded, reply))

    def thumbnail_downloaded(self, reply):
        self.queued_replies.remove(reply)
        if reply.error() == QNetworkReply.NoError:
            url = reply.url().toString()
            img = QImage()
            img.loadFromData(reply.readAll())
            self.thumbnails[url] = img
            self.downloaded.emit(url)


class ThumbnailManager:
    def __init__(self):
        self.thumbnails = {}
        self.widgets = defaultdict(list)
        self.widget_processors: Dict[object, ThumbnailProcessor] = {}
        self.queued_replies = set()

    def downloadThumbnail(self,
                          url: str,
                          widget,
                          processor: Optional[ThumbnailProcessor] = None):
        if not url and processor:
            thumbnail = processor.process_thumbnail(None)
            widget.setThumbnail(thumbnail)
            return

        if url in self.thumbnails:
            thumbnail = self.thumbnails[url]
            if processor:
                thumbnail = processor.process_thumbnail(thumbnail)
            widget.setThumbnail(thumbnail)
        else:
            self.widgets[url].append(widget)
            if processor:
                self.widget_processors[widget] = processor

            req = QNetworkRequest(QUrl(url))
            req.setAttribute(QNetworkRequest.CacheLoadControlAttribute, QNetworkRequest.PreferCache)
            req.setAttribute(QNetworkRequest.CacheSaveControlAttribute, True)
            reply = QgsNetworkAccessManager.instance().get(req)
            self.queued_replies.add(reply)
            if reply.isFinished():
                self.thumbnailDownloaded(reply)
            else:
                reply.finished.connect(partial(self.thumbnailDownloaded, reply))

    def thumbnailDownloaded(self, reply):
        self.queued_replies.remove(reply)
        if reply.error() == QNetworkReply.NoError:
            url = reply.url().toString()
            img = QImage()
            img.loadFromData(reply.readAll())
            self.thumbnails[url] = img
            for w in self.widgets[url]:
                thumbnail_image = QImage(img)
                if w in self.widget_processors:
                    thumbnail_image = \
                        self.widget_processors[w].process_thumbnail(
                            thumbnail_image
                        )
                    del self.widget_processors[w]

                try:
                    w.setThumbnail(thumbnail_image)
                except Exception:
                    # the widget might have been deleted
                    pass


_thumbnailManager = ThumbnailManager()


def downloadThumbnail(url: str,
                      widget,
                      processor: Optional[ThumbnailProcessor] = None):
    _thumbnailManager.downloadThumbnail(url, widget, processor)
