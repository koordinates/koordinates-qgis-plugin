from typing import Dict

from qgis.core import (
    QgsApplication
)
from qgis.utils import iface

from .client import KoordinatesClient
from .dataset import Dataset


class LayerUtils:
    """
    Layer handling utility functions
    """

    WMTS_URL_BASE = 'https://data.linz.govt.nz/services'
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
    def add_layer_to_project(dataset: Dataset):
        """
        Adds the layer to the current project from a dataset definition
        """
        color_name = LayerUtils.get_random_color_string()

        apikey = KoordinatesClient.instance().apiKey
        dataset_id = dataset.id

        uri = (
            "contextualWMSLegend=0&crs=EPSG:3857&dpiMode=7&format=image/png"
            f"&layers=layer-{dataset_id}&styles=style%3Dauto,"
            f"color%3D{color_name}&tileMatrixSet=EPSG:3857&"
            f"tilePixelRatio=0&url={LayerUtils.WMTS_URL_BASE};"
            f"key%3D{apikey}/{LayerUtils.WMTS_ENDPOINT}/"
            f"{dataset_id}/WMTSCapabilities.xml"
        )
        iface.addRasterLayer(uri, dataset.title(), "wms")
