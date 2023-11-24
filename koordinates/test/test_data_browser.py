# coding=utf-8
"""Tests Data Browser API.

.. note:: This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; either version 2 of the License, or
(at your option) any later version.
"""

__author__ = 'Nyall Dawson <nyall@north-road.com>'
__revision__ = '$Format:%H$'
__date__ = '12/09/2022'
__license__ = "GPL"
__copyright__ = 'Copyright 2022, Koordinates'

import unittest

from qgis.PyQt.QtCore import (
    QDate,
    QTime,
    QDateTime
)

from ..api import (
    DataBrowserQuery,
    DataType,
    VectorFilter,
    RasterFilter,
    RasterFilterOptions,
    RasterBandFilter,
    GridFilterOptions,
    CreativeCommonLicenseVersions,
    AccessType,
    SortOrder,
    Capability
)


class TestDataBrowser(unittest.TestCase):
    """
    Test the data browser api
    """

    def test_query(self):
        query = DataBrowserQuery()
        query.search = 'my filter'
        self.assertEqual(query.build_query(),
                         {'sort': 'popularity', 'q': 'my filter',
                          'kind': ['layer', 'table', 'set', 'document']})

    def test_starred(self):
        query = DataBrowserQuery()
        query.starred = True
        self.assertEqual(query.build_query(),
                         {'sort': 'popularity', 'is_starred': True,
                          'kind': ['layer', 'table', 'set', 'document']})

    def test_access(self):
        query = DataBrowserQuery()
        query.access_type = AccessType.Private
        self.assertEqual(query.build_query(),
                         {'sort': 'popularity', 'public': False,
                          'kind': ['layer', 'table', 'set', 'document']})
        query.access_type = AccessType.Public
        self.assertEqual(query.build_query(),
                         {'sort': 'popularity', 'public': True,
                          'kind': ['layer', 'table', 'set', 'document']})

    def test_category(self):
        query = DataBrowserQuery()
        query.category = 'my filter'
        self.assertEqual(query.build_query(),
                         {'sort': 'popularity', 'category': 'my filter',
                          'kind': ['layer', 'table', 'set', 'document']})

    def test_data_type_to_string(self):
        self.assertEqual(DataType.to_filter_strings(DataType.Vectors),
                         ['vector'])
        self.assertEqual(DataType.to_filter_strings(DataType.Rasters),
                         ['raster'])
        self.assertEqual(DataType.to_filter_strings(DataType.Grids),
                         ['grid', 'attribute-grid'])
        self.assertEqual(DataType.to_filter_strings(DataType.Tables),
                         ['table'])
        self.assertEqual(DataType.to_filter_strings(DataType.PointClouds),
                         ['pointcloud'])
        self.assertEqual(DataType.to_filter_strings(DataType.Sets),
                         ['set'])
        self.assertEqual(DataType.to_filter_strings(DataType.Repositories),
                         ['repo'])
        self.assertEqual(DataType.to_filter_strings(DataType.Documents),
                         ['document'])

    def test_data_from_string(self):
        self.assertEqual(DataType.from_string('vector'), DataType.Vectors)
        self.assertEqual(DataType.from_string('raster'), DataType.Rasters)
        self.assertEqual(DataType.from_string('grid'), DataType.Grids)
        self.assertEqual(DataType.from_string('attribute-grid'),
                         DataType.Grids)
        self.assertEqual(DataType.from_string('table'), DataType.Tables)
        self.assertEqual(DataType.from_string('pointcloud'), DataType.PointClouds)
        self.assertEqual(DataType.from_string('set'), DataType.Sets)
        self.assertEqual(DataType.from_string('repo'), DataType.Repositories)
        self.assertEqual(DataType.from_string('document'), DataType.Documents)

    def test_kind(self):
        query = DataBrowserQuery()
        query.data_types = {DataType.Rasters}
        self.assertEqual(query.build_query(), {'sort': 'popularity', 'kind': 'raster'})
        query.data_types = {DataType.Grids}
        self.assertEqual(query.build_query(),
                         {'sort': 'popularity', 'kind': ['attribute-grid', 'grid']})
        query.data_types = {DataType.PointClouds}
        self.assertEqual(query.build_query(), {'sort': 'popularity', 'kind': 'pointcloud'})
        query.data_types = {DataType.Tables}
        self.assertEqual(query.build_query(), {'sort': 'popularity', 'kind': 'table'})
        query.data_types = {DataType.Sets}
        self.assertEqual(query.build_query(), {'sort': 'popularity', 'kind': 'set'})
        query.data_types = {DataType.Repositories}
        self.assertEqual(query.build_query(), {'sort': 'popularity', 'kind': 'repo'})
        query.data_types = {DataType.Documents}
        self.assertEqual(query.build_query(), {'sort': 'popularity', 'kind': 'document'})
        # combined
        query.data_types = {DataType.Repositories, DataType.PointClouds}
        self.assertEqual(query.build_query(),
                         {'sort': 'popularity', 'kind': ['pointcloud', 'repo']})

    def test_vector_filters(self):
        query = DataBrowserQuery()
        query.data_types = {DataType.Vectors}
        query.vector_filters = {VectorFilter.Point}
        self.assertEqual(query.build_query(),
                         {'sort': 'popularity', 'data.geometry_type': 'point'})
        query.vector_filters = {VectorFilter.Line}
        self.assertEqual(query.build_query(),
                         {'sort': 'popularity', 'data.geometry_type': 'linestring'})
        query.vector_filters = {VectorFilter.Polygon}
        self.assertEqual(query.build_query(),
                         {'sort': 'popularity', 'data.geometry_type': 'polygon'})
        query.vector_filters = {VectorFilter.Polygon, VectorFilter.Line}
        self.assertEqual(query.build_query(),
                         {'sort': 'popularity', 'data.geometry_type': ['linestring', 'polygon']})

        query.vector_filters = {VectorFilter.HasZ}
        self.assertEqual(query.build_query(),
                         {'sort': 'popularity', 'has_z': True,
                          'data.geometry_type': ['point', 'linestring', 'polygon']})

        query.vector_filters = {VectorFilter.HasPrimaryKey}
        self.assertEqual(query.build_query(),
                         {'sort': 'popularity', 'has_pk': True,
                          'data.geometry_type': ['point', 'linestring', 'polygon']})

        # combined
        query.vector_filters = {VectorFilter.HasZ, VectorFilter.HasPrimaryKey, VectorFilter.Point}
        self.assertEqual(query.build_query(),
                         {'sort': 'popularity', 'data.geometry_type': 'point', 'has_pk': True,
                          'has_z': True})

    def test_raster_filters(self):
        query = DataBrowserQuery()
        query.data_types = {DataType.Rasters}
        query.raster_filters = {RasterFilter.AerialSatellitePhotos}
        self.assertEqual(query.build_query(),
                         {'sort': 'popularity', 'is_imagery': True, 'kind': 'raster'})
        query.raster_filters = {RasterFilter.NotAerialSatellitePhotos}
        self.assertEqual(query.build_query(),
                         {'sort': 'popularity', 'is_imagery': False, 'kind': 'raster'})
        query.raster_filters = {RasterFilter.ByBand}
        self.assertEqual(query.build_query(),
                         {'sort': 'popularity', 'kind': 'raster'})
        query.raster_band_filters = {RasterBandFilter.RGB}
        self.assertEqual(query.build_query(),
                         {'sort': 'popularity', 'raster_band': ['blue', 'green', 'red'],
                          'kind': 'raster'})
        query.raster_band_filters = {RasterBandFilter.BlackAndWhite}
        self.assertEqual(query.build_query(),
                         {'sort': 'popularity', 'raster_band': 'gray', 'kind': 'raster'})
        query.raster_filter_options = {RasterFilterOptions.WithAlphaChannel}
        self.assertEqual(query.build_query(),
                         {'sort': 'popularity', 'raster_band': ['alpha', 'gray'],
                          'kind': 'raster'})
        query.raster_band_filters = {RasterBandFilter.RGB}
        self.assertEqual(query.build_query(),
                         {'sort': 'popularity', 'raster_band': ['alpha', 'blue', 'green', 'red'],
                          'kind': 'raster'})

        query.raster_filters = {RasterFilter.NotAerialSatellitePhotos}
        self.assertEqual(query.build_query(),
                         {'sort': 'popularity', 'is_imagery': False, 'raster_band': 'alpha',
                          'kind': 'raster'})

        query.data_types = {DataType.Rasters}

        # resolution filters
        query.maximum_resolution = 10000
        self.assertEqual(query.build_query(), {'sort': 'popularity', 'is_imagery': False,
                                               'kind': 'raster',
                                               'raster_band': 'alpha',
                                               'raster_resolution.lt': 10000})
        query.maximum_resolution = None
        query.minimum_resolution = 20000
        self.assertEqual(query.build_query(), {'sort': 'popularity', 'is_imagery': False,
                                               'kind': 'raster',
                                               'raster_band': 'alpha',
                                               'raster_resolution.gt': 20000})
        query.maximum_resolution = 30000
        self.assertEqual(query.build_query(), {'sort': 'popularity', 'is_imagery': False,
                                               'kind': 'raster',
                                               'raster_band': 'alpha',
                                               'raster_resolution.gt': 20000,
                                               'raster_resolution.lt': 30000})
        query.maximum_resolution = 20000
        self.assertEqual(query.build_query(),
                         {'sort': 'popularity', 'is_imagery': False, 'kind': 'raster',
                          'raster_band': 'alpha'})

        query.data_types = {DataType.Rasters, DataType.Grids}
        self.assertEqual(query.build_query(),
                         {'sort': 'popularity', 'is_imagery': False,
                          'kind': ['attribute-grid', 'grid', 'raster']})

    def test_grid_filters(self):
        query = DataBrowserQuery()
        query.data_types = {DataType.Grids}
        self.assertEqual(query.build_query(),
                         {'sort': 'popularity', 'kind': ['attribute-grid', 'grid']})
        query.grid_filter_options = {GridFilterOptions.MultiAttributeGridsOnly}
        self.assertEqual(query.build_query(), {'sort': 'popularity', 'kind': 'attribute-grid'})
        query.data_types = {DataType.Grids, DataType.Rasters}
        self.assertEqual(query.build_query(),
                         {'sort': 'popularity', 'kind': ['attribute-grid', 'raster']})

    def test_table_filter(self):
        query = DataBrowserQuery()
        query.data_types = {DataType.Tables}
        self.assertEqual(query.build_query(), {'sort': 'popularity', 'kind': 'table'})
        query.vector_filters.add(VectorFilter.HasPrimaryKey)
        self.assertEqual(query.build_query(),
                         {'sort': 'popularity', 'kind': 'table', 'has_pk': True})

    def test_date_filters(self):
        query = DataBrowserQuery()
        query.created_minimum = QDateTime(QDate(2022, 1, 3), QTime(0, 0, 0))
        self.assertEqual(query.build_query(),
                         {'sort': 'popularity', 'created_at.after': '2022-01-03T00:00:00',
                          'kind': ['layer', 'table', 'set', 'document']})
        query.created_minimum = None
        query.created_maximum = QDateTime(QDate(2022, 1, 3), QTime(0, 0, 0))
        self.assertEqual(query.build_query(),
                         {'sort': 'popularity', 'created_at.before': '2022-01-03T00:00:00',
                          'kind': ['layer', 'table', 'set', 'document']})
        query.created_maximum = None
        query.updated_minimum = QDateTime(QDate(2022, 1, 3), QTime(0, 0, 0))
        self.assertEqual(query.build_query(),
                         {'sort': 'popularity', 'updated_at.after': '2022-01-03T00:00:00',
                          'kind': ['layer', 'table', 'set', 'document']})
        query.updated_minimum = None
        query.updated_maximum = QDateTime(QDate(2022, 1, 3), QTime(0, 0, 0))
        self.assertEqual(query.build_query(),
                         {'sort': 'popularity', 'updated_at.before': '2022-01-03T00:00:00',
                          'kind': ['layer', 'table', 'set', 'document']})
        query.updated_minimum = QDateTime(QDate(2020, 1, 3), QTime(0, 0, 0))
        self.assertEqual(query.build_query(),
                         {'sort': 'popularity', 'updated_at.after': '2020-01-03T00:00:00',
                          'updated_at.before': '2022-01-03T00:00:00',
                          'kind': ['layer', 'table', 'set', 'document']})

    def test_license_filters(self):
        query = DataBrowserQuery()

        query.cc_license_versions = {CreativeCommonLicenseVersions.Version3}
        self.assertEqual(query.build_query(), {'sort': 'popularity', 'license.version': '3.0',
                                               'kind': ['layer', 'table', 'set', 'document']})
        query.cc_license_versions = {CreativeCommonLicenseVersions.Version4}
        self.assertEqual(query.build_query(), {'sort': 'popularity', 'license.version': '4.0',
                                               'kind': ['layer', 'table', 'set', 'document']})
        query.cc_license_versions = {CreativeCommonLicenseVersions.Version3,
                                     CreativeCommonLicenseVersions.Version4}
        self.assertEqual(query.build_query(),
                         {'sort': 'popularity', 'license.version': ['3.0', '4.0'],
                          'kind': ['layer', 'table', 'set', 'document']})

        query.cc_license_versions = {CreativeCommonLicenseVersions.Version3}
        query.cc_license_allow_derivates = True
        self.assertEqual(query.build_query(),
                         {'sort': 'popularity', 'license.type': '-cc-by-nd',
                          'license.version': '3.0',
                          'kind': ['layer', 'table', 'set', 'document']})
        query.cc_license_allow_derivates = False
        self.assertEqual(query.build_query(),
                         {'sort': 'popularity', 'license.type': 'cc-by-nd',
                          'license.version': '3.0',
                          'kind': ['layer', 'table', 'set', 'document']})
        query.cc_license_allow_derivates = None

        query.cc_license_allow_commercial = True
        self.assertEqual(query.build_query(),
                         {'sort': 'popularity', 'license.type': '-cc-by-nc',
                          'license.version': '3.0',
                          'kind': ['layer', 'table', 'set', 'document']})
        query.cc_license_allow_commercial = False
        self.assertEqual(query.build_query(),
                         {'sort': 'popularity', 'license.type': 'cc-by-nc',
                          'license.version': '3.0',
                          'kind': ['layer', 'table', 'set', 'document']})
        query.cc_license_allow_commercial = None

        query.cc_license_changes_must_be_shared = True
        self.assertEqual(query.build_query(),
                         {'sort': 'popularity', 'license.type': 'cc-by-sa',
                          'license.version': '3.0',
                          'kind': ['layer', 'table', 'set', 'document']})
        query.cc_license_changes_must_be_shared = False
        self.assertEqual(query.build_query(),
                         {'sort': 'popularity', 'license.type': '-cc-by-sa',
                          'license.version': '3.0',
                          'kind': ['layer', 'table', 'set', 'document']})
        query.cc_license_allow_commercial = True
        self.assertEqual(query.build_query(),
                         {'sort': 'popularity', 'license.type': ['-cc-by-nc', '-cc-by-sa'],
                          'license.version': '3.0',
                          'kind': ['layer', 'table', 'set', 'document']})

    def test_sort(self):
        query = DataBrowserQuery()
        query.order = SortOrder.Popularity
        self.assertEqual(query.build_query(),
                         {'sort': 'popularity', 'kind': ['layer', 'table', 'set', 'document']})
        query.popular_order_string = 'AU'
        self.assertEqual(query.build_query(),
                         {'sort': 'popularity', 'country':'AU',
                          'country_boost': 6, 'multiplier_boost': True,
                          'kind': ['layer', 'table', 'set', 'document']})
        query.order = SortOrder.RecentlyAdded
        self.assertEqual(query.build_query(),
                         {'sort': 'created_at', 'kind': ['layer', 'table', 'set', 'document']})
        query.order = SortOrder.RecentlyUpdated
        self.assertEqual(query.build_query(),
                         {'sort': 'updated_at', 'kind': ['layer', 'table', 'set', 'document']})
        query.order = SortOrder.AlphabeticalAZ
        self.assertEqual(query.build_query(),
                         {'sort': 'name', 'kind': ['layer', 'table', 'set', 'document']})
        query.order = SortOrder.AlphabeticalZA
        self.assertEqual(query.build_query(),
                         {'sort': '-name', 'kind': ['layer', 'table', 'set', 'document']})
        query.order = SortOrder.Oldest
        self.assertEqual(query.build_query(),
                         {'sort': '-created_at', 'kind': ['layer', 'table', 'set', 'document']})

        self.assertEqual(SortOrder.to_text(SortOrder.Popularity), 'Popularity')
        self.assertEqual(SortOrder.to_text(SortOrder.RecentlyAdded), 'Recently Added')
        self.assertEqual(SortOrder.to_text(SortOrder.RecentlyUpdated), 'Recently Updated')
        self.assertEqual(SortOrder.to_text(SortOrder.AlphabeticalAZ), 'Alphabetical (A-Z)')
        self.assertEqual(SortOrder.to_text(SortOrder.AlphabeticalZA), 'Alphabetical (Z-A)')
        self.assertEqual(SortOrder.to_text(SortOrder.Oldest), 'Oldest')

    def test_capabilities(self):
        """
        Test capabilities for different data types
        """
        self.assertEqual(DataType.capabilities(DataType.Vectors),
                         {Capability.Clone,
                          Capability.Add,
                          Capability.RevisionCount})
        self.assertEqual(DataType.capabilities(DataType.Rasters),
                         {Capability.Clone,
                          Capability.Add,
                          Capability.RevisionCount})
        self.assertEqual(DataType.capabilities(DataType.Grids),
                         {Capability.Clone,
                          Capability.Add,
                          Capability.RevisionCount})
        self.assertEqual(DataType.capabilities(DataType.Sets),
                         {Capability.Clone,
                          Capability.RevisionCount})
        self.assertEqual(DataType.capabilities(DataType.Tables),
                         {Capability.Clone,
                          Capability.RevisionCount})
        self.assertEqual(DataType.capabilities(DataType.Documents),
                         {Capability.Clone,
                          Capability.RevisionCount})
        self.assertEqual(DataType.capabilities(DataType.Repositories),
                         {Capability.Clone,
                          Capability.RevisionCount})
        self.assertEqual(DataType.capabilities(DataType.PointClouds),
                         {Capability.Clone,
                          Capability.Add})


if __name__ == '__main__':
    unittest.main()
