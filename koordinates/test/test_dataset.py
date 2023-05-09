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

import os
import tempfile
import unittest

from .utilities import get_qgis_app
from ..api import (
    Dataset,
    DataType,
    Capability
)

QGIS_APP = get_qgis_app()


class TestDataset(unittest.TestCase):
    """
    Test the Dataset class
    """

    def test_point_cloud(self):
        """
        Test point cloud datasets
        """
        with tempfile.TemporaryDirectory() as tmpdirname:
            print('created temporary directory', tmpdirname)
            with open(os.path.join(tmpdirname, 'repo.json'), 'wt') as f:
                f.write("""
{
    "id": "vqMgDm3",
    "full_name": "koordinates/kx-pc-kapti-laz",
    "url": "https://test.koordinates.com/services/api/v1.x/repos/koordinates/aaa-laz/",
    "clone_location_ssh": "kart@data.koordinates.com:koordinates/aaa-laz",
    "clone_location_https": "https://test.koordinates.com/koordinates/aaa-laz",
    "type": "repo",
    "title": "Some repo",
    "first_published_at": "2022-11-30T22:01:56.979877Z",
    "published_at": null,
    "settings": {
        "feedback_enabled": true
    },
    "user_permissions": [
        "find",
        "view",
        "download",
        "write"
    ],
    "name": "some repo name",
    "description": ""
}
                """)

            point_cloud_dataset = Dataset(
                {
                    'url_html': 'https://test.koordinates.com/layer/aaa/bbb/',
                    'id': 'aaa',
                    'repository': 'file://{}'.format(
                        os.path.join(tmpdirname, 'repo.json')),
                    'path': 'bbb',
                    'url': 'https://test.koordinates.com/services/api/v1.x/datasets/ccc/',
                    'title': 'TestPointCloud',
                    'updated_at_commit': 'aaabbb',
                    'updated_at': '2022-10-14T00:09:21Z',
                    'ref': 'refs/heads/main',
                    'type': 'layer', 'kind': 'pointcloud',
                    'public_access': None,
                    'settings': {'feedback_enabled': True},
                    'user_permissions': ['find', 'view', 'download', 'write'],
                    'description': '', 'description_html': '',
                    'created_at_commit': '298f43b4d81c113f8311b10e186dc32983220a55',
                    'created_at': '2022-10-14T00:09:21Z'
                }
            )
            self.assertEqual(point_cloud_dataset.datatype,
                             DataType.PointClouds)
            self.assertEqual(point_cloud_dataset.repository().clone_url(),
                             'https://test.koordinates.com/koordinates/aaa-laz')
            self.assertEqual(point_cloud_dataset.id, 'aaa')
            self.assertEqual(point_cloud_dataset.capabilities,
                             {Capability.Clone, Capability.Add})
