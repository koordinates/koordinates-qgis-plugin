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
    ApiUtils
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


if __name__ == '__main__':
    unittest.main()
