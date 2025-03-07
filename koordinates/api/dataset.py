import datetime
from typing import (
    Dict,
    List,
    Optional
)

from dateutil import parser
from qgis.core import (
    QgsGeometry,
    QgsMapLayer,
    QgsRasterLayer,
    QgsFields,
    QgsMemoryProviderUtils,
    QgsCoordinateReferenceSystem,
    QgsFeature,
    QgsWkbTypes
)

from .enums import DataType
from .repo import Repo
from .utils import ApiUtils
from .publisher import Publisher


class Crs:
    """
    Represents a CRS
    """

    def __init__(self, details: Dict):
        self.details = details

    def name(self) -> Optional[str]:
        """
        Returns the CRS name
        """
        return self.details.get('name')

    def id(self) -> Optional[str]:
        """
        Returns the CRS ID
        """
        return self.details.get('id')

    def url_external(self) -> Optional[str]:
        """
        Returns the external URL for the CRS
        """
        return self.details.get('url_external')


class Style:
    """
    Represents a dataset's style
    """

    def __init__(self, details: Dict):
        self.details = details
        self.url: str = details['url']
        self.state: str = details['url']
        self.description: Optional[str] = details['description'] or None

    def id(self) -> int:
        """
        Returns the style ID
        """
        return self.details['id']

    def name(self) -> str:
        """
        Returns the style's name
        """
        return self.details['name']

    def url(self) -> str:
        """
        Returns the style's URL
        """
        return self.details['url']

    def description(self) -> Optional[str]:
        """
        Returns the optional style description
        """
        return self.details.get("description") or None

    def is_default(self) -> bool:
        """
        Returns True if the style is the default
        """
        return self.details.get('is_default', False)

    def created_at_date(self) -> Optional[datetime.date]:
        """
        Returns the created at date
        """
        created_at_date_str: Optional[str] = self.details.get(
            "created_at"
        )

        if created_at_date_str:
            return parser.parse(created_at_date_str)

        return None

    def published_at_date(self) -> Optional[datetime.date]:
        """
        Returns the published at date
        """
        published_at_date_str: Optional[str] = self.details.get(
            "published_at"
        )

        if published_at_date_str:
            return parser.parse(published_at_date_str)

        return None


class Dataset:
    """
    Represents a dataset
    """

    def __init__(self, details: Dict):
        self.details = details
        self.id = details['id']
        self.datatype = ApiUtils.data_type_from_dataset_response(self.details)
        self.geometry_type: QgsWkbTypes.GeometryType = \
            ApiUtils.geometry_type_from_dataset_response(
                self.details
            )

        self.capabilities = ApiUtils.capabilities_from_dataset_response(
            self.details
        )
        self.access = ApiUtils.access_from_dataset_response(self.details)
        self._repository: Optional[Repo] = None
        self._styles_retrieved = False
        self._styles: List[Style] = []

        self.gridded_extent: Optional[QgsGeometry] = None
        if 'data' in self.details and self.details['data'].get(
                'gridded_extent'):
            self.gridded_extent = ApiUtils.geometry_from_hexwkb(
                self.details['data']['gridded_extent']
            )

        self.crs: Optional[Crs] = Crs(self.details['data']['crs']) \
            if self.details.get('data', {}).get('crs') else None

    def title(self) -> str:
        """
        Returns the dataset's title
        """
        return self.details.get("title", 'Layer')

    def html_description(self) -> str:
        """
        Returns the HTML dataset description
        """
        return self.details.get("description_html", '')

    def url_canonical(self) -> Optional[str]:
        """
        Returns the canonical URL for the dataset
        """
        return self.details.get('url_canonical')

    def publisher(self) -> Optional[Publisher]:
        """
        Returns the publisher details
        """
        if not self.details.get("publisher"):
            return None

        return Publisher(self.details["publisher"])

    def is_starred(self) -> bool:
        """
        Returns True if the dataset is starred
        """
        return self.details.get('is_starred', False)

    def thumbnail_url(self) -> Optional[str]:
        """
        Returns the dataset's thumbnail URL
        """
        return self.details.get('thumbnail_url')

    def created_at_date(self) -> Optional[datetime.date]:
        """
        Returns the created at / first published at date
        """
        created_at_date_str: Optional[str] = self.details.get(
            "first_published_at"
        )
        if not created_at_date_str:
            created_at_date_str = self.details.get("created_at")

        if created_at_date_str:
            return parser.parse(created_at_date_str)

        return None

    def updated_at_date(self) -> Optional[datetime.date]:
        """
        Returns the updated at date
        """
        updated_at_date_str: Optional[str] = self.details.get("updated_at")
        if not updated_at_date_str:
            updated_at_date_str = self.details.get("published_at")

        if updated_at_date_str:
            return parser.parse(updated_at_date_str)

        return None

    def number_downloads(self) -> int:
        """
        Returns the number of dataset downloads
        """
        return self.details.get("num_downloads", 0)

    def number_views(self) -> int:
        """
        Returns the number of dataset views
        """
        return self.details.get("num_views", 0)

    def repository(self) -> Optional[Repo]:
        """
        Returns the repository information for the dataset
        """

        if self._repository is not None:
            return self._repository

        if self.datatype == DataType.Repositories:
            # Set repository for the existing dataset detail:
            self._repository = Repo(self.details)

        else:
            repo_detail_url = self.details.get("repository")
            if repo_detail_url and isinstance(repo_detail_url, dict):
                # Set repository from the already available repo detail:
                self._repository = Repo(repo_detail_url)
            elif repo_detail_url:
                # Set the repsository from the fetched repo detail response:
                from .client import KoordinatesClient

                self._repository = KoordinatesClient.instance().retrieve_repository(
                    repo_detail_url
                )

        return self._repository

    def styles(self) -> List[Style]:
        """
        Returns styles for the dataset
        """
        if self._styles_retrieved:
            return self._styles

        if isinstance(self.details.get('styles'), list):
            for result in self.details['styles']:
                self._styles.append(Style(result))
            self._styles_retrieved = True
            return self._styles

        style_url = self.details.get('styles')
        if not style_url:
            self._styles_retrieved = True
            return self._styles

        from .client import KoordinatesClient
        results = KoordinatesClient.instance().layer_styles(
            style_url
        )
        for result in results:
            self._styles.append(Style(result))
        self._styles_retrieved = True
        return self._styles

    def to_map_layer(self, style_id: Optional[int] = None) -> Optional[QgsMapLayer]:
        """
        Converts the dataset to a map layer, if possible
        """
        from .layer_utils import LayerUtils

        if self.datatype in (
                DataType.Vectors,
                DataType.Rasters,
                DataType.Grids):
            color_name = LayerUtils.get_random_color_string()

            from .client import KoordinatesClient
            apikey = KoordinatesClient.instance().apiKey

            style = 'auto' if style_id is None else str(style_id)

            uri = (
                "contextualWMSLegend=0&crs=EPSG:3857&dpiMode=7&format=image/png"
                f"&layers=layer-{self.id}&styles=style%3D{style},"
                f"color%3D{color_name}&tileMatrixSet=EPSG:3857&"
                f"tilePixelRatio=0&url={LayerUtils.WMTS_URL_BASE};"
                f"key%3D{apikey}/{LayerUtils.WMTS_ENDPOINT}/"
                f"{self.id}/WMTSCapabilities.xml"
            )
            res = QgsRasterLayer(uri, self.title(), "wms")
            # force feature mode for identify results by default --
            # see https://github.com/koordinates/koordinates-qgis-plugin/issues/239
            res.setCustomProperty('identify/format', 'Feature')
            return res

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
