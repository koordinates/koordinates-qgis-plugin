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
from qgis.PyQt.QtGui import QImage

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
        from .user_avatar_generator import UserAvatarGenerator

        if thumbnail and not thumbnail.isNull():
            if self.publisher.publisher_type == PublisherType.Publisher:
                max_thumbnail_width = self.size.width()
                max_thumbnail_height = \
                    int(min(self.size.height(),
                            thumbnail.height()))
                scaled = thumbnail.scaled(
                    QSize(max_thumbnail_width, max_thumbnail_height),
                    Qt.KeepAspectRatio,
                    Qt.SmoothTransformation)
            else:
                scaled = DatasetGuiUtils.crop_image_to_circle(
                    thumbnail, thumbnail.height()
                )
            return scaled

        elif self.publisher.publisher_type == PublisherType.User:
            thumbnail = UserAvatarGenerator.get_avatar(self.publisher.name())
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
            reply = QgsNetworkAccessManager.instance().get(QNetworkRequest(QUrl(url)))
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
        if url in self.thumbnails:
            thumbnail = self.thumbnails[url]
            if processor:
                thumbnail = processor.process_thumbnail(thumbnail)
            widget.setThumbnail(thumbnail)
        else:
            self.widgets[url].append(widget)
            if processor:
                self.widget_processors[widget] = processor
            reply = QgsNetworkAccessManager.instance().get(QNetworkRequest(QUrl(url)))
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
