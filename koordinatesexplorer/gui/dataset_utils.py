from enum import Enum
from typing import (
    Optional,
    Dict
)

from qgis.core import QgsFileUtils


class IconStyle(Enum):
    Dark = 0
    Light = 1


class DatasetGuiUtils:

    @staticmethod
    def get_icon_for_dataset(dataset: Dict, style: IconStyle) -> Optional[str]:
        if style == IconStyle.Light:
            suffix = 'light'
        else:
            suffix = 'dark'

        if dataset.get('type') == 'layer':
            if dataset.get('kind') == 'vector':
                if dataset.get('data', {}).get('geometry_type') in (
                        'polygon', 'multipolygon'):
                    return 'polygon-{}.svg'.format(suffix)
                elif dataset.get('data', {}).get('geometry_type') in ('point', 'multipoint'):
                    return 'point-{}.svg'.format(suffix)
                elif dataset.get('data', {}).get('geometry_type') in (
                        'linestring', 'multilinestring'):
                    return 'line-{}.svg'.format(suffix)
            elif dataset.get('kind') == 'raster':
                return 'raster-{}.svg'.format(suffix)
            elif dataset.get('kind') == 'grid':
                return 'grid-{}.svg'.format(suffix)
        elif dataset.get('type') == 'table':
            return 'table-{}.svg'.format(suffix)
        elif dataset.get('type') == 'document':
            return 'document-{}.svg'.format(suffix)
        elif dataset.get('type') == 'set':
            return 'set-{}.svg'.format(suffix)
        elif dataset.get('type') == 'repo':
            return 'repo-{}.svg'.format(suffix)

        return None

    @staticmethod
    def get_data_type(dataset: Dict) -> Optional[str]:
        if dataset.get('type') == 'layer':
            if dataset.get('kind') == 'vector':
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
            elif dataset.get('kind') == 'raster':
                return 'Raster'
            elif dataset.get('kind') == 'grid':
                return 'Grid'
        elif dataset.get('type') == 'table':
            return 'Table'
        elif dataset.get('type') == 'document':
            return 'Document'
        elif dataset.get('type') == 'set':
            return 'Set'
        elif dataset.get('type') == 'repo':
            return 'Repository'

        return None

    @staticmethod
    def get_type_description(dataset: Dict) -> Optional[str]:
        if dataset.get('type') == 'layer':
            if dataset.get('kind') == 'vector':
                if dataset.get('data', {}).get('geometry_type') in (
                        'polygon', 'multipolygon'):
                    return 'Polygon Layer'
                elif dataset.get('data', {}).get('geometry_type') in ('point', 'multipoint'):
                    return 'Point Layer'
                elif dataset.get('data', {}).get('geometry_type') in (
                        'linestring', 'multilinestring'):
                    return 'Line Layer'
            elif dataset.get('kind') == 'raster':
                return 'Raster Layer'
            elif dataset.get('kind') == 'grid':
                return 'Grid Layer'
        elif dataset.get('type') == 'table':
            return 'Table'
        elif dataset.get('type') == 'document':
            return 'Document'
        elif dataset.get('type') == 'set':
            return 'Set'
        elif dataset.get('type') == 'repo':
            return 'Repository'

        return None

    @staticmethod
    def get_subtitle(dataset: Dict) -> Optional[str]:
        if dataset.get('type') == 'layer':
            if dataset.get('kind') == 'vector':
                count = dataset["data"]["feature_count"]
                if dataset.get('data', {}).get('geometry_type') in (
                        'polygon', 'multipolygon'):
                    return '{} Polygons'.format(DatasetGuiUtils.format_count(count))
                elif dataset.get('data', {}).get('geometry_type') in ('point', 'multipoint'):
                    return '{} Points'.format(DatasetGuiUtils.format_count(count))
                elif dataset.get('data', {}).get('geometry_type') in (
                        'linestring', 'multilinestring'):
                    return '{} Lines'.format(DatasetGuiUtils.format_count(count))
            elif dataset.get('kind') in ('raster', 'grid'):
                count = dataset["data"]["feature_count"]
                res = dataset["data"]["raster_resolution"]
                return '{}m, {} Tiles'.format(res,
                                              DatasetGuiUtils.format_count(count))
        elif dataset.get('type') == 'table':
            count = dataset["data"]["feature_count"]
            return '{} Rows'.format(DatasetGuiUtils.format_count(count))
        elif dataset.get('type') == 'document':
            ext = dataset['extension'].upper()
            file_size = dataset['file_size']
            return '{} {}'.format(ext, QgsFileUtils.representFileSize(file_size))
        elif dataset.get('type') == 'set':
            return None
        elif dataset.get('type') == 'repo':
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
