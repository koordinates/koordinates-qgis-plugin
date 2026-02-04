"""
Qt5/Qt6 compatibility layer for PyQt imports
"""

from qgis.PyQt.QtGui import (
    QPixmap,
    QFontMetrics as _QFontMetrics,
    QFontDatabase as _QFontDatabase,
)
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
        if hasattr(super(), "horizontalAdvance"):
            # Qt6
            if length >= 0:
                return self.horizontalAdvance(text, length)
            return self.horizontalAdvance(text)
        else:
            # Qt5
            if length >= 0:
                return super().width(text, length)
            return super().width(text)


def fontmetric_width(fm, text: str) -> int:
    """Get text width from QFontMetrics, compatible with Qt5 and Qt6"""
    if hasattr(fm, "horizontalAdvance"):
        return fm.horizontalAdvance(text)
    return fm.width(text)


def font_families():
    """Get list of font families, compatible with Qt5 and Qt6"""
    families_attr = getattr(_QFontDatabase, "families", None)
    if families_attr and callable(families_attr):
        # Qt6 - static method
        return _QFontDatabase.families()
    else:
        # Qt5 - instance method
        return _QFontDatabase().families()


__all__ = ["QSvgWidget", "QFontMetrics", "fontmetric_width", "font_families"]
