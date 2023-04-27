# coding=utf-8
"""Tests API utils

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

from ..api import (
    ApiUtils,
    DataType,
    Capability
)


class TestApiUtils(unittest.TestCase):
    """
    Test the API utilities
    """

    def test_to_url_query(self):
        self.assertEqual(ApiUtils.to_url_query({}).toString(), '')
        self.assertEqual(ApiUtils.to_url_query({'param1': 'value1',
                                                'param2': 'value2'}).toString(),
                         'param1=value1&param2=value2')
        self.assertEqual(ApiUtils.to_url_query({'param1': ['value1', 'value2'],
                                                'param2': 'value3',
                                                'param3': 3}).toString(),
                         'param1=value1&param1=value2&param2=value3&param3=3')

    def test_data_type(self):
        """
        Test retrieving data type from response
        """
        self.assertEqual(ApiUtils.data_type_from_dataset_response(
            {
                'type': 'layer',
                'kind': 'vector'
            }), DataType.Vectors)
        self.assertEqual(ApiUtils.data_type_from_dataset_response(
            {
                'type': 'layer',
                'kind': 'raster'
            }), DataType.Rasters)
        self.assertEqual(ApiUtils.data_type_from_dataset_response(
            {
                'type': 'layer',
                'kind': 'grid'
            }), DataType.Grids)
        self.assertEqual(ApiUtils.data_type_from_dataset_response(
            {
                'type': 'layer',
                'kind': 'pointcloud'
            }), DataType.PointClouds)
        self.assertEqual(ApiUtils.data_type_from_dataset_response(
            {
                'type': 'table'
            }), DataType.Tables)
        self.assertEqual(ApiUtils.data_type_from_dataset_response(
            {
                'type': 'document'
            }), DataType.Documents)
        self.assertEqual(ApiUtils.data_type_from_dataset_response(
            {
                'type': 'set'
            }), DataType.Sets)
        self.assertEqual(ApiUtils.data_type_from_dataset_response(
            {
                'type': 'repo'
            }), DataType.Repositories)

    def test_capabilities(self):
        """
        Test retrieving capabilities from response
        """
        self.assertEqual(ApiUtils.capabilities_from_dataset_response(
            {
                'type': 'layer',
                'kind': 'vector',
                'repository': 'something'
            }), {Capability.Clone, Capability.Add, Capability.RevisionCount})
        self.assertEqual(ApiUtils.capabilities_from_dataset_response(
            {
                'type': 'layer',
                'kind': 'vector',
                'repository': None
            }), {Capability.Add, Capability.RevisionCount})
        self.assertEqual(ApiUtils.capabilities_from_dataset_response(
            {
                'type': 'layer',
                'kind': 'raster',
                'repository': 'something'
            }), {Capability.Clone, Capability.Add, Capability.RevisionCount})
        self.assertEqual(ApiUtils.capabilities_from_dataset_response(
            {
                'type': 'layer',
                'kind': 'raster'
            }), {Capability.Add, Capability.RevisionCount})
        self.assertEqual(ApiUtils.capabilities_from_dataset_response(
            {
                'type': 'layer',
                'kind': 'grid'
            }), {Capability.Add, Capability.RevisionCount})
        self.assertEqual(ApiUtils.capabilities_from_dataset_response(
            {
                'type': 'layer',
                'kind': 'grid',
                'repository': 'something'
            }), {Capability.Clone, Capability.Add, Capability.RevisionCount})
        self.assertEqual(ApiUtils.capabilities_from_dataset_response(
            {
                'type': 'table'
            }), {Capability.RevisionCount})
        self.assertEqual(ApiUtils.capabilities_from_dataset_response(
            {
                'type': 'table',
                'repository': 'something'
            }), {Capability.Clone, Capability.RevisionCount})
        self.assertEqual(ApiUtils.capabilities_from_dataset_response(
            {
                'type': 'document'
            }), {Capability.RevisionCount})
        self.assertEqual(ApiUtils.capabilities_from_dataset_response(
            {
                'type': 'document',
                'repository': 'something'
            }), {Capability.Clone, Capability.RevisionCount})
        self.assertEqual(ApiUtils.capabilities_from_dataset_response(
            {
                'type': 'set'
            }), {Capability.RevisionCount})
        self.assertEqual(ApiUtils.capabilities_from_dataset_response(
            {
                'type': 'set',
                'repository': 'something'
            }), {Capability.Clone, Capability.RevisionCount})
        self.assertEqual(ApiUtils.capabilities_from_dataset_response(
            {
                'type': 'repo'
            }), {Capability.RevisionCount})
        self.assertEqual(ApiUtils.capabilities_from_dataset_response(
            {
                'type': 'repo',
                'repository': 'something'
            }), {Capability.Clone, Capability.RevisionCount})
        self.assertEqual(ApiUtils.capabilities_from_dataset_response(
            {
                'type': 'layer',
                'kind': 'pointcloud',
                'repository': 'something'
            }), {Capability.Clone, Capability.Add})


if __name__ == '__main__':
    unittest.main()
