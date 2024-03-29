from typing import Dict, Set, Optional

from qgis.PyQt.QtCore import QDateTime, Qt

from .enums import (
    SortOrder,
    AccessType,
    VectorFilter,
    RasterFilter,
    DataType,
    RasterBandFilter,
    RasterFilterOptions,
    GridFilterOptions,
    CreativeCommonLicenseVersions,
    PublisherType
)
from .publisher import Publisher


class DataBrowserQuery:
    """
    Represents a query for data browser API
    """

    def __init__(self):

        self.order = SortOrder.Popularity
        self.popular_order_string: Optional[str] = None

        self.search: Optional[str] = None
        self.starred = False
        self.access_type: Optional[AccessType] = None
        self.category: Optional[str] = None
        self.group: Optional[str] = None

        self.publisher: Optional[Publisher] = None

        self.data_types: Set[DataType] = set()
        self.vector_filters: Set[VectorFilter] = set()
        self.raster_filters: Set[RasterFilter] = set()
        self.raster_band_filters: Set[RasterBandFilter] = set()
        self.raster_filter_options: Set[RasterFilterOptions] = set()
        self.grid_filter_options: Set[GridFilterOptions] = set()

        self.minimum_resolution: Optional[float] = None
        self.maximum_resolution: Optional[float] = None

        self.created_minimum: Optional[QDateTime] = None
        self.created_maximum: Optional[QDateTime] = None
        self.updated_minimum: Optional[QDateTime] = None
        self.updated_maximum: Optional[QDateTime] = None

        self.cc_license_versions: Set[CreativeCommonLicenseVersions] = set()
        self.cc_license_allow_derivates: Optional[bool] = None
        self.cc_license_allow_commercial: Optional[bool] = None
        self.cc_license_changes_must_be_shared: Optional[bool] = None

    def build_query(self) -> Dict[str, object]:
        """
        Builds the filter parameters into a query
        """
        params = {}

        if self.search:
            params['q'] = self.search

        if self.starred:
            params['is_starred'] = True

        if self.access_type is not None:
            if self.access_type == AccessType.Private:
                params['public'] = False
            elif self.access_type == AccessType.Public:
                params['public'] = True

        if self.category:
            params['category'] = self.category

        if self.group:
            params['group'] = self.group

        if self.publisher:
            if self.publisher.publisher_type == PublisherType.User:
                params['user'] = self.publisher.id()[len('user:'):]
            else:
                params['from'] = self.publisher.id()

        kind_params = []
        for data_type in self.data_types:
            if data_type == DataType.Vectors and self.vector_filters is not None:
                continue

            if data_type == DataType.Grids and \
                    GridFilterOptions.MultiAttributeGridsOnly in self.grid_filter_options:
                kind_params.append('attribute-grid')
                continue

            kind_params.extend(DataType.to_filter_strings(data_type))

        if len(kind_params) > 1:
            params["kind"] = sorted(kind_params)
        elif kind_params:
            params["kind"] = kind_params[0]

        geometry_params = []
        for vector_filter in self.vector_filters:
            if vector_filter == VectorFilter.Point:
                geometry_params.append('point')
            elif vector_filter == VectorFilter.Line:
                geometry_params.append('linestring')
            elif vector_filter == VectorFilter.Polygon:
                geometry_params.append('polygon')
            elif vector_filter == VectorFilter.HasZ:
                params['has_z'] = True
            elif vector_filter == VectorFilter.HasPrimaryKey:
                params['has_pk'] = True

        if len(geometry_params) > 1:
            params["data.geometry_type"] = sorted(geometry_params)
        elif geometry_params:
            params["data.geometry_type"] = geometry_params[0]

        raster_band_filters = []
        for raster_filter in self.raster_filters:
            if raster_filter == RasterFilter.AerialSatellitePhotos:
                params["is_imagery"] = True
            elif raster_filter == RasterFilter.NotAerialSatellitePhotos:
                params["is_imagery"] = False
            elif raster_filter == RasterFilter.ByBand:
                for raster_band_filter in self.raster_band_filters:
                    if raster_band_filter == RasterBandFilter.RGB:
                        raster_band_filters = ['red', 'green', 'blue']
                    elif raster_band_filter == RasterBandFilter.BlackAndWhite:
                        raster_band_filters = ['gray']

        if RasterFilterOptions.WithAlphaChannel in self.raster_filter_options \
                and self.data_types == {DataType.Rasters}:
            raster_band_filters.append('alpha')

        if len(raster_band_filters) > 1:
            params["raster_band"] = sorted(raster_band_filters)
        elif raster_band_filters:
            params["raster_band"] = raster_band_filters[0]

        if self.data_types == {DataType.Rasters} or self.data_types == {DataType.Grids}:
            if self.maximum_resolution != self.minimum_resolution:
                if self.minimum_resolution is not None:
                    params["raster_resolution.gt"] = self.minimum_resolution
                if self.maximum_resolution is not None:
                    params["raster_resolution.lt"] = self.maximum_resolution

        if self.created_maximum:
            params["created_at.before"] = QDateTime(self.created_maximum.date()).toString(
                Qt.ISODate
            )
        if self.created_minimum:
            params["created_at.after"] = QDateTime(self.created_minimum.date()).toString(
                Qt.ISODate
            )
        if self.updated_maximum:
            params["updated_at.before"] = QDateTime(self.updated_maximum.date()).toString(
                Qt.ISODate
            )
        if self.updated_minimum:
            params["updated_at.after"] = QDateTime(self.updated_minimum.date()).toString(
                Qt.ISODate
            )

        cc_license_versions = []
        for version in self.cc_license_versions:
            if version == CreativeCommonLicenseVersions.Version3:
                cc_license_versions.append('3.0')
            elif version == CreativeCommonLicenseVersions.Version4:
                cc_license_versions.append('4.0')

        if len(cc_license_versions) > 1:
            params["license.version"] = sorted(cc_license_versions)
        elif cc_license_versions:
            params["license.version"] = cc_license_versions[0]

        license_types = []
        if self.cc_license_allow_derivates is not None:
            if self.cc_license_allow_derivates:
                license_types.append('-cc-by-nd')
            else:
                license_types.append('cc-by-nd')
        if self.cc_license_allow_commercial is not None:
            if self.cc_license_allow_commercial:
                license_types.append('-cc-by-nc')
            else:
                license_types.append('cc-by-nc')
        if self.cc_license_changes_must_be_shared is not None:
            if self.cc_license_changes_must_be_shared:
                license_types.append('cc-by-sa')
            else:
                license_types.append('-cc-by-sa')

        if len(license_types) > 1:
            params["license.type"] = sorted(license_types)
        elif license_types:
            params["license.type"] = license_types[0]

        # extra query logic for defaults:
        # 1. If no filters are active, the query string is initialized to the default data types
        if 'kind' not in params and DataType.Vectors not in self.data_types:
            params['kind'] = ['layer', 'table', 'set', 'document']

        # 2. If there are filters active, but nothing for `kind` or `data.geometry_type`
        # then the query string has the default data types appended to it
        if 'data.geometry_type' not in params and DataType.Vectors in self.data_types:
            params['data.geometry_type'] = ['point', 'linestring', 'polygon']

        # 3. If intersite data is enabled, and there are no active filters blocking
        # intersite data (presence of `from`, `org`, or `user` query params) then the
        # query string has `from=all` appended to it

        # 4. If we are filtering to a country (presence of `country` query param)
        # then the query string has `country_boost=4` appended to it

        # 5. If we are filtering to a geotag (presence of `geotag` query param)
        # then the query string has `geotag_boost=10` appended to it

        if self.order == SortOrder.Popularity:
            params['sort'] = 'popularity'
            if self.popular_order_string:
                params['country'] = self.popular_order_string
                params['country_boost'] = 6
                params['multiplier_boost'] = True
        elif self.order == SortOrder.RecentlyAdded:
            params['sort'] = 'created_at'
        elif self.order == SortOrder.RecentlyUpdated:
            params['sort'] = 'updated_at'
        elif self.order == SortOrder.AlphabeticalAZ:
            params['sort'] = 'name'
        elif self.order == SortOrder.AlphabeticalZA:
            params['sort'] = '-name'
        elif self.order == SortOrder.Oldest:
            params['sort'] = '-created_at'

        return params
