# coding=utf-8
"""Tests Repo

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
    Repo
)


class TestRepo(unittest.TestCase):
    """
    Test the Repo class
    """

    def test_repo(self):
        """
        Test basic properties
        """
        r = Repo(
            {
                "id": "111",
                "full_name": "koordinates/aaa",
                "url": "https://test.koordinates.com/services/api/v1.x/repos/koordinates/aaa/",
                "clone_location_ssh": "kart@data.koordinates.com:koordinates/aaa",
                "clone_location_https": "https://data.koordinates.com/koordinates/aaa",
                "type": "repo",
                "title": "Title",
                "first_published_at": "2022-10-17T20:22:32.754753Z",
                "name": "Name",
                "description": "Description",
            }
        )
        self.assertEqual(r.clone_url(),
                         'https://data.koordinates.com/koordinates/aaa')
