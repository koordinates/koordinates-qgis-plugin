"""
Qt5/Qt6 compatibility layer for PyQt imports
"""

from qgis.PyQt.QtCore import QSize
from qgis.PyQt.QtGui import QPixmap, QFontMetrics as _QFontMetrics
from qgis.PyQt.QtSvg import QSvgRenderer
from qgis.PyQt.QtWidgets import QLabel

# QSvgWidget is in QtSvg in Qt5, but moved to QtSvgWidgets in Qt6.
# QGIS doesn't wrap QtSvgWidgets, so use QLabel-based fallback for Qt6.
try:
    from qgis.PyQt.QtSvg import QSvgWidget
except ImportError:
    # Qt6/QGIS fallback: QLabel-based implementation
    class QSvgWidget(QLabel):
        """QSvgWidget replacement using QLabel + QSvgRenderer for Qt6 compatibility"""

        def __init__(self, parent=None):
            super().__init__(parent)
            self._svg_path = None
            self._renderer = None

        def load(self, path: str | bytes | None):
            """Load SVG from file path or bytes"""
            if path is None:
                self.clear()
                self._svg_path = None
                self._renderer = None
                return

            self._svg_path = path
            self._renderer = QSvgRenderer(path)
            self._render_svg()

        def _render_svg(self):
            """Render SVG to pixmap"""
            if not self._renderer or not self._renderer.isValid():
                return

            size = self.size()
            if size.width() <= 0 or size.height() <= 0:
                # Use default size if widget size not set
                size = self._renderer.defaultSize()

            pixmap = QPixmap(size)
            pixmap.fill(self.palette().color(self.backgroundRole()))

            from qgis.PyQt.QtGui import QPainter
            painter = QPainter(pixmap)
            self._renderer.render(painter)
            painter.end()

            self.setPixmap(pixmap)

        def resizeEvent(self, event):
            """Re-render on resize"""
            super().resizeEvent(event)
            if self._renderer:
                self._render_svg()


# QFontMetrics.width() renamed to horizontalAdvance() in Qt6
class QFontMetrics(_QFontMetrics):
    """QFontMetrics wrapper providing Qt5/Qt6 compatibility for width() method"""

    def width(self, text: str, length: int = -1) -> int:
        """Qt5-compatible width() method that calls horizontalAdvance() in Qt6"""
        if hasattr(super(), 'horizontalAdvance'):
            # Qt6
            return self.horizontalAdvance(text, length) if length >= 0 else self.horizontalAdvance(text)
        else:
            # Qt5
            return super().width(text, length) if length >= 0 else super().width(text)


def fontmetric_width(fm, text: str) -> int:
    """Get text width from QFontMetrics, compatible with Qt5 and Qt6"""
    return fm.horizontalAdvance(text) if hasattr(fm, 'horizontalAdvance') else fm.width(text)


# QFontDatabase changed from instance methods to static methods in Qt6
from qgis.PyQt.QtGui import QFontDatabase as _QFontDatabase


def font_families():
    """Get list of font families, compatible with Qt5 and Qt6"""
    if hasattr(_QFontDatabase, 'families') and callable(getattr(_QFontDatabase, 'families')):
        # Qt6 - static method
        return _QFontDatabase.families()
    else:
        # Qt5 - instance method
        return _QFontDatabase().families()


__all__ = ['QSvgWidget', 'QFontMetrics', 'fontmetric_width', 'font_families']
