from typing import (
    Dict,
    Optional
)
import base64

from qgis.PyQt.QtGui import QIcon


class ExploreSection:
    """
    Represents an explore section
    """

    DEFAULT_SECTION = 'popular'

    def __init__(self, details: Dict):
        self.details = details

        self.label = self.details.get('label')
        self.description = self.details.get('description')
        self.slug = self.details.get('slug')
        self.icon: Optional[QIcon] = None

        icon_url = self.details.get('icon_url')

        from .client import KoordinatesClient
        from ..gui.gui_utils import GuiUtils

        if isinstance(icon_url, str) and \
                icon_url.startswith(
                    KoordinatesClient.BASE64_ENCODED_SVG_HEADER):
            base64_content = icon_url[
                             len(KoordinatesClient.BASE64_ENCODED_SVG_HEADER):]
            svg_content = base64.b64decode(base64_content)
            self.icon = GuiUtils.svg_to_icon(svg_content)
