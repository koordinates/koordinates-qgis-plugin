from enum import Enum
from typing import (
    Set,
    List
)


class AccessType(Enum):
    """
    Access types
    """
    Public = 1
    Private = 2


class PublicAccessType(Enum):
    """
    Public access types
    """
    none = 1
    Download = 2


class Capability(Enum):
    """
    Dataset capabilities
    """
    Clone = 0
    Add = 1


class DataType(Enum):
    """
    Data types
    """
    Vectors = 1
    Rasters = 2
    Grids = 3
    PointClouds = 4
    Tables = 5
    Sets = 6
    Repositories = 7
    Documents = 8

    @staticmethod
    def capabilities(data_type: 'DataType') -> Set[Capability]:
        """
        Returns capabilities for a data type
        """
        if data_type in (DataType.Vectors,
                         DataType.Rasters,
                         DataType.Grids,
                         DataType.PointClouds):
            return {Capability.Add, Capability.Clone}

        return {Capability.Clone}

    @staticmethod
    def to_filter_strings(data_type: 'DataType') -> List[str]:
        """
        Converts a data type to a string list of matching filter strings
        """
        return {
            DataType.Vectors: ['vector'],
            DataType.Rasters: ['raster'],
            DataType.Grids: ['grid', 'attribute-grid'],
            DataType.PointClouds: ['pointcloud'],
            DataType.Tables: ['table'],
            DataType.Sets: ['set'],
            DataType.Repositories: ['repo'],
            DataType.Documents: ['document'],
        }[data_type]

    @staticmethod
    def from_string(string: str) -> 'DataType':
        """
        Returns a data type from a response string
        """
        return {
            'vector': DataType.Vectors,
            'raster': DataType.Rasters,
            'grid': DataType.Grids,
            'attribute-grid': DataType.Grids,
            'pointcloud': DataType.PointClouds,
            'table': DataType.Tables,
            'set': DataType.Sets,
            'repo': DataType.Repositories,
            'document': DataType.Documents,
        }[string]

    def identifier_string(self) -> str:
        """
        Returns a user friendly string identifying the data type, eg 'layer'
        or 'dataset'
        """
        return {
            DataType.Vectors: 'Layer',
            DataType.Rasters: 'Layer',
            DataType.Grids: 'Layer',
            DataType.PointClouds: 'Dataset',
            DataType.Tables: 'Dataset',
            DataType.Sets: 'Dataset',
            DataType.Repositories: 'Dataset',
            DataType.Documents: 'Dataset',
        }[self]



class VectorFilter(Enum):
    """
    Vector filter options
    """
    Point = 1
    Line = 2
    Polygon = 3
    HasZ = 4
    HasPrimaryKey = 5


class RasterFilter(Enum):
    """
    Raster filter options
    """
    AerialSatellitePhotos = 1
    NotAerialSatellitePhotos = 2
    ByBand = 3


class RasterBandFilter(Enum):
    """
    Raster band filters
    """
    RGB = 1
    BlackAndWhite = 2


class RasterFilterOptions(Enum):
    """
    Additional raster filter options
    """
    WithAlphaChannel = 1


class GridFilterOptions(Enum):
    """
    Additional grid filter options
    """
    MultiAttributeGridsOnly = 1


class CreativeCommonLicenseVersions(Enum):
    """
    CC license version
    """
    Version3 = 3
    Version4 = 4


class SortOrder(Enum):
    """
    Sorting options
    """
    Popularity = 1
    RecentlyAdded = 2
    RecentlyUpdated = 3
    AlphabeticalAZ = 4
    AlphabeticalZA = 5
    Oldest = 6

    @staticmethod
    def to_text(order: 'SortOrder'):
        """
        Converts sort order to user-friendly text
        """
        return {SortOrder.Popularity: 'Popularity',
                SortOrder.RecentlyAdded: 'Recently Added',
                SortOrder.RecentlyUpdated: 'Recently Updated',
                SortOrder.AlphabeticalAZ: 'Alphabetical (A-Z)',
                SortOrder.AlphabeticalZA: 'Alphabetical (Z-A)',
                SortOrder.Oldest: 'Oldest'}[order]
