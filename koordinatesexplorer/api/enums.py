from enum import Enum


class AccessType(Enum):
    """
    Access types
    """
    Public = 1
    Private = 2


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
