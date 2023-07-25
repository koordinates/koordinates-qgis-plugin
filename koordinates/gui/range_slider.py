import platform
from qgis.PyQt.QtCore import QSize
from qgis.gui import QgsRangeSlider


class RangeSlider(QgsRangeSlider):
    """
    Avoids a crash when non-standard application themes are used on the
    mac platform.

    Relates to https://bugreports.qt.io/browse/QTBUG-43398
    https://bugreports.qt.io/browse/QTBUG-44316?focusedCommentId=272257
    """

    def sizeHint(self):
        if platform.system() == 'Darwin':
            # sizeHint crashes on mac for hidden QSlider widgets
            return QSize(100, 30)

        return super().sizeHint()
