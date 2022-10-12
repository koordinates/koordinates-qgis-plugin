# coding=utf-8
"""Tests dataset browser

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

from ..gui.datasetsbrowserwidget import (
    DatasetItemWidget
)


class TestDatasetBrowser(unittest.TestCase):
    """
    Test the dataset browser
    """

    def test_format_count(self):
        self.assertEqual(DatasetItemWidget.format_count(0), '0')
        self.assertEqual(DatasetItemWidget.format_count(1), '1')
        self.assertEqual(DatasetItemWidget.format_count(9), '9')
        self.assertEqual(DatasetItemWidget.format_count(10), '10')
        self.assertEqual(DatasetItemWidget.format_count(101), '101')
        self.assertEqual(DatasetItemWidget.format_count(999), '999')
        self.assertEqual(DatasetItemWidget.format_count(1000), '1K')
        self.assertEqual(DatasetItemWidget.format_count(1001), '1K')
        self.assertEqual(DatasetItemWidget.format_count(1010), '1K')
        self.assertEqual(DatasetItemWidget.format_count(1100), '1.1K')
        self.assertEqual(DatasetItemWidget.format_count(1300), '1.3K')
        self.assertEqual(DatasetItemWidget.format_count(1700), '1.7K')
        self.assertEqual(DatasetItemWidget.format_count(1999), '1.9K')
        self.assertEqual(DatasetItemWidget.format_count(2000), '2K')
        self.assertEqual(DatasetItemWidget.format_count(2200), '2.2K')
        self.assertEqual(DatasetItemWidget.format_count(9200), '9.2K')
        self.assertEqual(DatasetItemWidget.format_count(9900), '9.9K')
        self.assertEqual(DatasetItemWidget.format_count(10000), '10K')
        self.assertEqual(DatasetItemWidget.format_count(10100), '10.1K')
        self.assertEqual(DatasetItemWidget.format_count(11000), '11K')
        self.assertEqual(DatasetItemWidget.format_count(482300), '482.3K')
        self.assertEqual(DatasetItemWidget.format_count(999999), '999.9K')
        self.assertEqual(DatasetItemWidget.format_count(1000000), '1M')
        self.assertEqual(DatasetItemWidget.format_count(1000001), '1M')
        self.assertEqual(DatasetItemWidget.format_count(1100000), '1.1M')
        self.assertEqual(DatasetItemWidget.format_count(10000000), '10M')


if __name__ == '__main__':
    unittest.main()
