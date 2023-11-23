from typing import Optional

from qgis.core import (
    QgsApplication,
    QgsProject
)

from .dataset import Dataset


class LayerUtils:
    """
    Layer handling utility functions
    """

    WMTS_URL_BASE = 'https://koordinates.com/services'
    WMTS_ENDPOINT = 'wmts/1.0.0/layer'

    @staticmethod
    def get_random_color_string() -> str:
        """
        Returns a random color string to use for a new layer
        """
        color = QgsApplication.colorSchemeRegistry().fetchRandomStyleColor()
        # string '#' from color name
        return color.name()[1:]

    @staticmethod
    def add_layer_to_project(
            dataset: Dataset,
            style_id: Optional[int] = None):
        """
        Adds the layer to the current project from a dataset definition
        """
        layer = dataset.to_map_layer(style_id=style_id)
        if layer:
            QgsProject.instance().addMapLayer(layer)
