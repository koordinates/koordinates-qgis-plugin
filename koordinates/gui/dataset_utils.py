from enum import Enum
from typing import (
    Optional
)
import locale
import datetime

from qgis.core import (
    QgsFileUtils,
    QgsWkbTypes
)

from ..api import (
    DataType,
    Dataset
)


class IconStyle(Enum):
    Dark = 0
    Light = 1


class DatasetGuiUtils:

    @staticmethod
    def thumbnail_icon_for_dataset(dataset: Dataset) -> Optional[str]:
        """
        Returns the name of the SVG thumbnail graphic for datasets which
        have a fixed thumbnail
        """
        if dataset.datatype == DataType.Repositories:
            return 'repository-image.svg'
        if dataset.datatype == DataType.PointClouds:
            return 'point-cloud-image.svg'
        return None

    @staticmethod
    def get_icon_for_dataset(dataset: Dataset, style: IconStyle) \
            -> Optional[str]:
        if style == IconStyle.Light:
            suffix = 'light'
        else:
            suffix = 'dark'

        if dataset.datatype == DataType.Vectors:
            if dataset.geometry_type == QgsWkbTypes.PolygonGeometry:
                return 'polygon-{}.svg'.format(suffix)
            elif dataset.geometry_type == QgsWkbTypes.PointGeometry:
                return 'point-{}.svg'.format(suffix)
            elif dataset.geometry_type == QgsWkbTypes.LineGeometry:
                return 'line-{}.svg'.format(suffix)
        elif dataset.datatype == DataType.Rasters:
            return 'raster-{}.svg'.format(suffix)
        elif dataset.datatype == DataType.Grids:
            return 'grid-{}.svg'.format(suffix)
        elif dataset.datatype == DataType.Tables:
            return 'table-{}.svg'.format(suffix)
        elif dataset.datatype == DataType.Documents:
            return 'document-{}.svg'.format(suffix)
        elif dataset.datatype == DataType.Sets:
            return 'set-{}.svg'.format(suffix)
        elif dataset.datatype == DataType.Repositories:
            return 'repo-{}.svg'.format(suffix)
        elif dataset.datatype == DataType.PointClouds:
            return 'point-cloud-{}.svg'.format(suffix)

        return None

    @staticmethod
    def get_data_type(dataset: Dataset) -> Optional[str]:
        if dataset.datatype == DataType.Vectors:
            if dataset.details.get('data', {}).get(
                    'geometry_type') == 'polygon':
                return 'Vector polygon'
            elif dataset.details.get('data', {}).get(
                    'geometry_type') == 'multipolygon':
                return 'Vector multipolygon'
            elif dataset.details.get('data', {}).get(
                    'geometry_type') == 'point':
                return 'Vector point'
            elif dataset.details.get('data', {}).get(
                    'geometry_type') == 'multipoint':
                return 'Vector multipoint'
            elif dataset.details.get('data', {}).get(
                    'geometry_type') == 'linestring':
                return 'Vector line'
            elif dataset.details.get('data', {}).get(
                    'geometry_type') == 'multilinestring':
                return 'Vector multiline'
        elif dataset.datatype == DataType.Rasters:
            return 'Raster'
        elif dataset.datatype == DataType.Grids:
            return 'Grid'
        elif dataset.datatype == DataType.Tables:
            return 'Table'
        elif dataset.datatype == DataType.Documents:
            return 'Document'
        elif dataset.datatype == DataType.Sets:
            return 'Set'
        elif dataset.datatype == DataType.Repositories:
            return 'Repository'
        elif dataset.datatype == DataType.PointClouds:
            return 'Point cloud'

        return None

    @staticmethod
    def get_type_description(dataset: Dataset) -> Optional[str]:
        if dataset.datatype == DataType.Vectors:
            if dataset.geometry_type == QgsWkbTypes.PolygonGeometry:
                return 'Polygon Layer'
            elif dataset.geometry_type == QgsWkbTypes.PointGeometry:
                return 'Point Layer'
            elif dataset.geometry_type == QgsWkbTypes.LineGeometry:
                return 'Line Layer'
        elif dataset.datatype == DataType.Rasters:
            return 'Raster Layer'
        elif dataset.datatype == DataType.Grids:
            return 'Grid Layer'
        elif dataset.datatype == DataType.Tables:
            return 'Table'
        elif dataset.datatype == DataType.Documents:
            return 'Document'
        elif dataset.datatype == DataType.Sets:
            return 'Set'
        elif dataset.datatype == DataType.Repositories:
            return 'Repository'
        elif dataset.datatype == DataType.PointClouds:
            return 'Point Cloud'

        return None

    @staticmethod
    def get_subtitle(dataset: Dataset, short_format: bool = True) \
            -> Optional[str]:
        """
        Return a subtitle to use for a Dataset
        """
        if dataset.datatype == DataType.Vectors:

            count = dataset.details.get("data", {}).get("feature_count") or 0

            if dataset.geometry_type == QgsWkbTypes.PolygonGeometry:
                return '{} Polygons'.format(
                    DatasetGuiUtils.format_count(count))
            elif dataset.geometry_type == QgsWkbTypes.PointGeometry:
                return '{} Points'.format(DatasetGuiUtils.format_count(count))
            elif dataset.geometry_type == QgsWkbTypes.LineGeometry:
                return '{} Lines'.format(DatasetGuiUtils.format_count(count))
        elif dataset.datatype in (DataType.Rasters, DataType.Grids):
            count = dataset.details.get("data", {}).get("feature_count") or 0
            res = dataset.details.get("data", {}).get("raster_resolution") or 0
            return '{}m, {} Tiles'.format(res,
                                          DatasetGuiUtils.format_count(count))
        elif dataset.datatype == DataType.Tables:
            count = dataset.details.get("data", {}).get("feature_count") or 0
            return '{} Rows'.format(DatasetGuiUtils.format_count(count))
        elif dataset.datatype == DataType.Documents:
            ext = dataset.details.get('extension', '').upper()
            file_size = dataset.details.get('file_size')
            if file_size:
                return '{} {}'.format(ext, QgsFileUtils.representFileSize(
                    file_size))
            return ext
        elif dataset.datatype == DataType.Sets:
            return None
        elif dataset.datatype == DataType.Repositories:
            return None
        elif dataset.datatype == DataType.PointClouds:
            count = dataset.details.get("data", {}).get("feature_count") or 0
            point_count = dataset.details.get("data", {}).get(
                "point_count") or 0
            if short_format:
                return '{} Tiles'.format(
                    DatasetGuiUtils.format_count(count)
                )
            else:
                return '{} Points, {} Tiles'.format(
                    DatasetGuiUtils.format_count(point_count),
                    DatasetGuiUtils.format_count(count)
                )

        return None

    @staticmethod
    def format_number(value):
        """
        Formats a number for localised display
        """
        return locale.format_string("%d", value, grouping=True)

    @staticmethod
    def format_date(value: datetime.date):
        """
        Formats a date value for display
        """
        return value.strftime("%d %b %Y")

    @staticmethod
    def format_count(count: int) -> str:
        """
        Pretty formats a rounded count
        """
        if count >= 1000000:
            rounded = ((count * 10) // 1000000) / 10
            if int(rounded) == rounded:
                rounded = int(rounded)

            return str(rounded) + 'M'

        if count >= 1000:
            rounded = ((count * 10) // 1000) / 10
            if int(rounded) == rounded:
                rounded = int(rounded)

            return str(rounded) + 'K'

        return str(count)
