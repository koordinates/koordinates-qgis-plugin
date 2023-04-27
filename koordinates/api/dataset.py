import datetime
from dateutil import parser
from typing import (
    Dict,
    Optional
)

from qgis.core import (
    QgsGeometry,
    QgsMapLayer,
    QgsRasterLayer,
    QgsFields,
    QgsMemoryProviderUtils,
    QgsCoordinateReferenceSystem,
    QgsFeature
)

from .utils import ApiUtils
from .client import KoordinatesClient
from .repo import Repo
from .enums import  DataType


class Dataset:
    """
    Represents a dataset
    """

    def __init__(self, details: Dict):
        self.details = details
        self.id = details['id']
        self.datatype = ApiUtils.data_type_from_dataset_response(self.details)

        self.capabilities = ApiUtils.capabilities_from_dataset_response(
            self.details
        )
        self.access = ApiUtils.access_from_dataset_response(self.details)
        self.repository: Optional[Repo] = None

        self.gridded_extent: Optional[QgsGeometry] = None
        if 'data' in self.details and self.details['data'].get('gridded_extent'):
            self.gridded_extent = ApiUtils.geometry_from_hexewkb(
                self.details['data']['gridded_extent']
            )

    def title(self) -> str:
        """
        Returns the dataset's title
        """
        return self.details.get("title", 'Layer')

    def publisher_name(self) -> Optional[str]:
        """
        Returns the publisher name
        """
        return self.details.get("publisher", {}).get("name")

    def is_starred(self) -> bool:
        """
        Returns True if the dataset is starred
        """
        return self.details.get('is_starred', False)

    def published_at_date(self) -> Optional[datetime.date]:
        """
        Returns the published at date
        """
        published_at_date_str: Optional[str] = self.details.get("published_at")
        if published_at_date_str:
            return parser.parse(published_at_date_str)

        return None

    def updated_at_date(self) -> Optional[datetime.date]:
        """
        Returns the updated at date
        """
        updated_at_date_str: Optional[str] = self.details.get("updated_at")
        if updated_at_date_str:
            return parser.parse(updated_at_date_str)

        return None

    def clone_url(self) -> Optional[str]:
        """
        Returns the clone URL for the dataset
        """
        if self.repository is not None:
            return self.repository.clone_url()

        if isinstance(self.details.get("repository"), dict):
            url = self.details["repository"].get("clone_location_https")
            if url:
                return url

        repo_detail_url = self.details.get('repository')
        if repo_detail_url:
            self.repository = KoordinatesClient.instance().retrieve_repository(
                repo_detail_url
            )
        if self.repository:
            return self.repository.clone_url()

        return None

    def to_map_layer(self) -> Optional[QgsMapLayer]:
        """
        Converts the dataset to a map layer, if possible
        """
        from .layer_utils import LayerUtils

        if self.datatype in (DataType.Vectors, DataType.Rasters, DataType.Grids):
            color_name = LayerUtils.get_random_color_string()

            apikey = KoordinatesClient.instance().apiKey

            uri = (
                "contextualWMSLegend=0&crs=EPSG:3857&dpiMode=7&format=image/png"
                f"&layers=layer-{self.id}&styles=style%3Dauto,"
                f"color%3D{color_name}&tileMatrixSet=EPSG:3857&"
                f"tilePixelRatio=0&url={LayerUtils.WMTS_URL_BASE};"
                f"key%3D{apikey}/{LayerUtils.WMTS_ENDPOINT}/"
                f"{self.id}/WMTSCapabilities.xml"
            )
            return QgsRasterLayer(uri, self.title(), "wms")

        if self.datatype in (DataType.PointClouds,) and self.gridded_extent:
            layer = QgsMemoryProviderUtils.createMemoryLayer(
                self.title(),
                QgsFields(),
                self.gridded_extent.wkbType(),
                QgsCoordinateReferenceSystem('EPSG:4326')
            )
            feature = QgsFeature()
            feature.setGeometry(self.gridded_extent)
            layer.dataProvider().addFeature(feature)
            return layer
