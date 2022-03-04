from collections import defaultdict

from PyQt5.QtNetwork import QNetworkAccessManager, QNetworkReply, QNetworkRequest
from qgis.PyQt.QtCore import QUrl
from qgis.PyQt.QtGui import QImage


class ThumbnailManager:
    def __init__(self):
        self.nam = QNetworkAccessManager()
        self.nam.finished.connect(self.thumbnailDownloaded)
        self.thumbnails = {}
        self.widgets = defaultdict(list)

    def downloadThumbnail(self, url, widget):
        if url in self.thumbnails:
            widget.setThumbnail(self.thumbnails[url])
        else:
            self.widgets[url].append(widget)
            self.nam.get(QNetworkRequest(QUrl(url)))

    def thumbnailDownloaded(self, reply):
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
