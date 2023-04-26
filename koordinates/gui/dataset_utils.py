from enum import Enum
from typing import (
    Optional,
    Dict
)

from qgis.core import QgsFileUtils

from ..api import (
    ApiUtils,
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
    def get_icon_for_dataset(dataset: Dict, style: IconStyle) -> Optional[str]:
        if style == IconStyle.Light:
            suffix = 'light'
        else:
            suffix = 'dark'

        data_type = ApiUtils.data_type_from_dataset_response(dataset)

        if data_type == DataType.Vectors:
            if dataset.get('data', {}).get('geometry_type') in (
                    'polygon', 'multipolygon'):
                return 'polygon-{}.svg'.format(suffix)
            elif dataset.get('data', {}).get('geometry_type') in ('point', 'multipoint'):
                return 'point-{}.svg'.format(suffix)
            elif dataset.get('data', {}).get('geometry_type') in (
                    'linestring', 'multilinestring'):
                return 'line-{}.svg'.format(suffix)
        elif data_type == DataType.Rasters:
            return 'raster-{}.svg'.format(suffix)
        elif data_type == DataType.Grids:
            return 'grid-{}.svg'.format(suffix)
        elif data_type == DataType.Tables:
            return 'table-{}.svg'.format(suffix)
        elif data_type == DataType.Documents:
            return 'document-{}.svg'.format(suffix)
        elif data_type == DataType.Sets:
            return 'set-{}.svg'.format(suffix)
        elif data_type == DataType.Repositories:
            return 'repo-{}.svg'.format(suffix)

        return None

    @staticmethod
    def get_data_type(dataset: Dict) -> Optional[str]:
        data_type = ApiUtils.data_type_from_dataset_response(dataset)
        if data_type == DataType.Vectors:
            if dataset.get('data', {}).get('geometry_type') == 'polygon':
                return 'Vector polygon'
            elif dataset.get('data', {}).get('geometry_type') == 'multipolygon':
                return 'Vector multipolygon'
            elif dataset.get('data', {}).get('geometry_type') == 'point':
                return 'Vector point'
            elif dataset.get('data', {}).get('geometry_type') == 'multipoint':
                return 'Vector multipoint'
            elif dataset.get('data', {}).get('geometry_type') == 'linestring':
                return 'Vector line'
            elif dataset.get('data', {}).get('geometry_type') == 'multilinestring':
                return 'Vector multiline'
        elif data_type == DataType.Rasters:
            return 'Raster'
        elif data_type == DataType.Grids:
            return 'Grid'
        elif data_type == DataType.Tables:
            return 'Table'
        elif data_type == DataType.Documents:
            return 'Document'
        elif data_type == DataType.Sets:
            return 'Set'
        elif data_type == DataType.Repositories:
            return 'Repository'

        return None

    @staticmethod
    def get_type_description(dataset: Dict) -> Optional[str]:
        data_type = ApiUtils.data_type_from_dataset_response(dataset)
        if data_type == DataType.Vectors:
            if dataset.get('data', {}).get('geometry_type') in (
                    'polygon', 'multipolygon'):
                return 'Polygon Layer'
            elif dataset.get('data', {}).get('geometry_type') in ('point', 'multipoint'):
                return 'Point Layer'
            elif dataset.get('data', {}).get('geometry_type') in (
                    'linestring', 'multilinestring'):
                return 'Line Layer'
        elif data_type == DataType.Rasters:
            return 'Raster Layer'
        elif data_type == DataType.Grids:
            return 'Grid Layer'
        elif data_type == DataType.Tables:
            return 'Table'
        elif data_type == DataType.Documents:
            return 'Document'
        elif data_type == DataType.Sets:
            return 'Set'
        elif data_type == DataType.Repositories:
            return 'Repository'

        return None

    @staticmethod
    def get_subtitle(dataset: Dict) -> Optional[str]:
        data_type = ApiUtils.data_type_from_dataset_response(dataset)
        if data_type == DataType.Vectors:

            count = dataset.get("data", {}).get("feature_count") or 0

            if dataset.get('data', {}).get('geometry_type') in (
                    'polygon', 'multipolygon'):
                return '{} Polygons'.format(DatasetGuiUtils.format_count(count))
            elif dataset.get('data', {}).get('geometry_type') in ('point', 'multipoint'):
                return '{} Points'.format(DatasetGuiUtils.format_count(count))
            elif dataset.get('data', {}).get('geometry_type') in (
                    'linestring', 'multilinestring'):
                return '{} Lines'.format(DatasetGuiUtils.format_count(count))
        elif data_type in (DataType.Rasters, DataType.Grids):
            count = dataset.get("data", {}).get("feature_count") or 0
            res = dataset.get("data", {}).get("raster_resolution") or 0
            return '{}m, {} Tiles'.format(res,
                                          DatasetGuiUtils.format_count(count))
        elif data_type == DataType.Tables:
            count = dataset.get("data", {}).get("feature_count") or 0
            return '{} Rows'.format(DatasetGuiUtils.format_count(count))
        elif data_type == DataType.Documents:
            ext = dataset.get('extension', '').upper()
            file_size = dataset.get('file_size')
            if file_size:
                return '{} {}'.format(ext, QgsFileUtils.representFileSize(file_size))
            return ext
        elif data_type == DataType.Sets:
            return None
        elif data_type == DataType.Repositories:
            return None

        return None

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
