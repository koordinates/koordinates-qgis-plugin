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
    AccessType
)


class TestDataBrowser(unittest.TestCase):
    """
    Test the data browser api
    """

    def test_query(self):
        query = DataBrowserQuery()
        self.assertEqual(query.build_query(), {})
        query.search = 'my filter'
        self.assertEqual(query.build_query(), {'q': 'my filter'})

    def test_starred(self):
        query = DataBrowserQuery()
        self.assertEqual(query.build_query(), {})
        query.starred = True
        self.assertEqual(query.build_query(), {'is_starred': True})

    def test_access(self):
        query = DataBrowserQuery()
        self.assertEqual(query.build_query(), {})
        query.access_type = AccessType.Private
        self.assertEqual(query.build_query(), {'public': False})
        query.access_type = AccessType.Public
        self.assertEqual(query.build_query(), {'public': True})

    def test_category(self):
        query = DataBrowserQuery()
        self.assertEqual(query.build_query(), {})
        query.category = 'my filter'
        self.assertEqual(query.build_query(), {'category': 'my filter'})

    def test_data_type_to_string(self):
        self.assertEqual(DataBrowserQuery.data_type_to_string(DataType.Vectors),
                         ['vector'])
        self.assertEqual(DataBrowserQuery.data_type_to_string(DataType.Rasters),
                         ['raster'])
        self.assertEqual(DataBrowserQuery.data_type_to_string(DataType.Grids),
                         ['grid', 'attribute-grid'])
        self.assertEqual(DataBrowserQuery.data_type_to_string(DataType.Tables),
                         ['table'])
        self.assertEqual(DataBrowserQuery.data_type_to_string(DataType.PointClouds),
                         ['pointcloud'])
        self.assertEqual(DataBrowserQuery.data_type_to_string(DataType.Sets),
                         ['set'])
        self.assertEqual(DataBrowserQuery.data_type_to_string(DataType.Repositories),
                         ['repo'])
        self.assertEqual(DataBrowserQuery.data_type_to_string(DataType.Documents),
                         ['document'])

    def test_kind(self):
        query = DataBrowserQuery()
        self.assertEqual(query.build_query(), {})
        query.data_types = {DataType.Rasters}
        self.assertEqual(query.build_query(), {'kind': 'raster'})
        query.data_types = {DataType.Grids}
        self.assertEqual(query.build_query(), {'kind': ['attribute-grid', 'grid']})
        query.data_types = {DataType.PointClouds}
        self.assertEqual(query.build_query(), {'kind': 'pointcloud'})
        query.data_types = {DataType.Tables}
        self.assertEqual(query.build_query(), {'kind': 'table'})
        query.data_types = {DataType.Sets}
        self.assertEqual(query.build_query(), {'kind': 'set'})
        query.data_types = {DataType.Repositories}
        self.assertEqual(query.build_query(), {'kind': 'repo'})
        query.data_types = {DataType.Documents}
        self.assertEqual(query.build_query(), {'kind': 'document'})
        # combined
        query.data_types = {DataType.Repositories, DataType.PointClouds}
        self.assertEqual(query.build_query(), {'kind': ['pointcloud', 'repo']})

    def test_vector_filters(self):
        query = DataBrowserQuery()
        self.assertEqual(query.build_query(), {})
        query.vector_filters = {VectorFilter.Point}
        self.assertEqual(query.build_query(), {'data.geometry_type': 'point'})
        query.vector_filters = {VectorFilter.Line}
        self.assertEqual(query.build_query(), {'data.geometry_type': 'linestring'})
        query.vector_filters = {VectorFilter.Polygon}
        self.assertEqual(query.build_query(), {'data.geometry_type': 'polygon'})
        query.vector_filters = {VectorFilter.Polygon, VectorFilter.Line}
        self.assertEqual(query.build_query(), {'data.geometry_type': ['linestring', 'polygon']})

        query.vector_filters = {VectorFilter.HasZ}
        self.assertEqual(query.build_query(), {'has_z': True})

        query.vector_filters = {VectorFilter.HasPrimaryKey}
        self.assertEqual(query.build_query(), {'has_pk': True})

        # combined
        query.vector_filters = {VectorFilter.HasZ, VectorFilter.HasPrimaryKey, VectorFilter.Point}
        self.assertEqual(query.build_query(),
                         {'data.geometry_type': 'point', 'has_pk': True, 'has_z': True})

    def test_raster_filters(self):
        query = DataBrowserQuery()
        self.assertEqual(query.build_query(), {})
        query.raster_filters = {RasterFilter.AerialSatellitePhotos}
        self.assertEqual(query.build_query(), {'is_imagery': True})
        query.raster_filters = {RasterFilter.NotAerialSatellitePhotos}
        self.assertEqual(query.build_query(), {'is_imagery': False})
        query.raster_filters = {RasterFilter.ByBand}
        self.assertEqual(query.build_query(), {})
        query.raster_band_filters = {RasterBandFilter.RGB}
        self.assertEqual(query.build_query(), {'raster_band': ['blue', 'green', 'red']})
        query.raster_band_filters = {RasterBandFilter.BlackAndWhite}
        self.assertEqual(query.build_query(), {'raster_band': 'gray'})
        query.raster_filter_options = {RasterFilterOptions.WithAlphaChannel}
        self.assertEqual(query.build_query(), {'raster_band': ['alpha', 'gray']})
        query.raster_band_filters = {RasterBandFilter.RGB}
        self.assertEqual(query.build_query(), {'raster_band': ['alpha', 'blue', 'green', 'red']})

        query.raster_filters = {RasterFilter.NotAerialSatellitePhotos}
        self.assertEqual(query.build_query(), {'is_imagery': False, 'raster_band': 'alpha'})

        query.data_types = {DataType.Rasters}

        # resolution filters
        query.maximum_resolution = 10000
        self.assertEqual(query.build_query(), {'is_imagery': False,
                                               'kind': 'raster',
                                               'raster_band': 'alpha',
                                               'raster_resolution.lt': 10000})
        query.maximum_resolution = None
        query.minimum_resolution = 20000
        self.assertEqual(query.build_query(), {'is_imagery': False,
                                               'kind': 'raster',
                                               'raster_band': 'alpha',
                                               'raster_resolution.gt': 20000})
        query.maximum_resolution = 30000
        self.assertEqual(query.build_query(), {'is_imagery': False,
                                               'kind': 'raster',
                                               'raster_band': 'alpha',
                                               'raster_resolution.gt': 20000,
                                               'raster_resolution.lt': 30000})
        query.maximum_resolution = 20000
        self.assertEqual(query.build_query(),
                         {'is_imagery': False, 'kind': 'raster', 'raster_band': 'alpha'})

    def test_grid_filters(self):
        query = DataBrowserQuery()
        self.assertEqual(query.build_query(), {})
        query.data_types = {DataType.Grids}
        self.assertEqual(query.build_query(), {'kind': ['attribute-grid', 'grid']})
        query.grid_filter_options = {GridFilterOptions.MultiAttributeGridsOnly}
        self.assertEqual(query.build_query(), {'kind': 'attribute-grid'})
        query.data_types = {DataType.Grids, DataType.Rasters}
        self.assertEqual(query.build_query(), {'kind': ['attribute-grid', 'raster']})

    def test_table_filter(self):
        query = DataBrowserQuery()
        self.assertEqual(query.build_query(), {})
        query.data_types = {DataType.Tables}
        self.assertEqual(query.build_query(), {'kind': 'table'})
        query.vector_filters.add(VectorFilter.HasPrimaryKey)
        self.assertEqual(query.build_query(), {'kind': 'table', 'has_pk': True})

    def test_date_filters(self):
        query = DataBrowserQuery()
        self.assertEqual(query.build_query(), {})
        query.created_minimum = QDateTime(QDate(2022, 1, 3), QTime(0, 0, 0))
        self.assertEqual(query.build_query(), {'created_at.after': '2022-01-03T00:00:00'})
        query.created_minimum = None
        query.created_maximum = QDateTime(QDate(2022, 1, 3), QTime(0, 0, 0))
        self.assertEqual(query.build_query(), {'created_at.before': '2022-01-03T00:00:00'})
        query.created_maximum = None
        query.updated_minimum = QDateTime(QDate(2022, 1, 3), QTime(0, 0, 0))
        self.assertEqual(query.build_query(), {'updated_at.after': '2022-01-03T00:00:00'})
        query.updated_minimum = None
        query.updated_maximum = QDateTime(QDate(2022, 1, 3), QTime(0, 0, 0))
        self.assertEqual(query.build_query(), {'updated_at.before': '2022-01-03T00:00:00'})
        query.updated_minimum = QDateTime(QDate(2020, 1, 3), QTime(0, 0, 0))
        self.assertEqual(query.build_query(), {'updated_at.after': '2020-01-03T00:00:00',
                                               'updated_at.before': '2022-01-03T00:00:00'})

    def test_license_filters(self):
        query = DataBrowserQuery()

        query.cc_license_versions = {CreativeCommonLicenseVersions.Version3}
        self.assertEqual(query.build_query(), {'license.version': '3.0'})
        query.cc_license_versions = {CreativeCommonLicenseVersions.Version4}
        self.assertEqual(query.build_query(), {'license.version': '4.0'})
        query.cc_license_versions = {CreativeCommonLicenseVersions.Version3,
                                     CreativeCommonLicenseVersions.Version4}
        self.assertEqual(query.build_query(), {'license.version': ['3.0', '4.0']})

        query.cc_license_versions = {CreativeCommonLicenseVersions.Version3}
        query.cc_license_allow_derivates = True
        self.assertEqual(query.build_query(),
                         {'license.type': '-cc-by-nd', 'license.version': '3.0'})
        query.cc_license_allow_derivates = False
        self.assertEqual(query.build_query(),
                         {'license.type': 'cc-by-nd', 'license.version': '3.0'})
        query.cc_license_allow_derivates = None

        query.cc_license_allow_commercial = True
        self.assertEqual(query.build_query(),
                         {'license.type': '-cc-by-nc', 'license.version': '3.0'})
        query.cc_license_allow_commercial = False
        self.assertEqual(query.build_query(),
                         {'license.type': 'cc-by-nc', 'license.version': '3.0'})
        query.cc_license_allow_commercial = None

        query.cc_license_changes_must_be_shared = True
        self.assertEqual(query.build_query(),
                         {'license.type': 'cc-by-sa', 'license.version': '3.0'})
        query.cc_license_changes_must_be_shared = False
        self.assertEqual(query.build_query(),
                         {'license.type': '-cc-by-sa', 'license.version': '3.0'})
        query.cc_license_allow_commercial = True
        self.assertEqual(query.build_query(),
                         {'license.type': ['-cc-by-nc', '-cc-by-sa'], 'license.version': '3.0'})


if __name__ == '__main__':
    unittest.main()
