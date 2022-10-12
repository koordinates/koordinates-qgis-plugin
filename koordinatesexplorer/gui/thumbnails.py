from collections import defaultdict

from functools import partial
from qgis.PyQt.QtNetwork import QNetworkReply, QNetworkRequest
from qgis.core import QgsNetworkAccessManager
from qgis.PyQt.QtCore import QUrl
from qgis.PyQt.QtGui import QImage


class ThumbnailManager:
    def __init__(self):
        self.thumbnails = {}
        self.widgets = defaultdict(list)
        self.queued_replies = set()

    def downloadThumbnail(self, url, widget):
        if url in self.thumbnails:
            widget.setThumbnail(self.thumbnails[url])
        else:
            self.widgets[url].append(widget)
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
                try:
                    w.setThumbnail(img)
                except Exception:
                    # the widget might have been deleted
                    pass


_thumbnailManager = ThumbnailManager()


def downloadThumbnail(url, widget):
    _thumbnailManager.downloadThumbnail(url, widget)
