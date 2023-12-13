"""Tests Filter Widgets

.. note:: This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; either version 2 of the License, or
(at your option) any later version.
"""

import unittest

from qgis.PyQt.QtCore import (
    QDate,
    QTime,
    QDateTime
)
from qgis.PyQt.QtTest import QSignalSpy

from ..api import (
    DataBrowserQuery,
    Publisher,
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
from ..gui.access_filter_widget import AccessFilterWidget
from ..gui.group_filter_widget import GroupFilterWidget
from ..gui.date_filter_widget import DateFilterWidget
from ..gui.license_filter_widget import LicenseFilterWidget
from ..gui.publisher_filter_widget import PublisherFilterWidget


from .utilities import get_qgis_app

QGIS_APP = get_qgis_app()

class TestFilterWidgets(unittest.TestCase):
    """
    Test filter widgets
    """

    def test_access_widget(self):
        w = AccessFilterWidget()

        # should start cleared
        self.assertFalse(w.should_show_clear())
        query = DataBrowserQuery()
        self.assertIsNone(query.access_type)
        w.apply_constraints_to_query(query)
        self.assertIsNone(query.access_type)

        spy = QSignalSpy(w.changed)
        # re-clearing already cleared should not emit signals
        w.clear()
        self.assertEqual(len(spy), 0)
        self.assertFalse(w.should_show_clear())

        # apply same query to widget, should be no signals
        w.set_from_query(query)
        self.assertEqual(len(spy), 0)
        w.apply_constraints_to_query(query)
        self.assertIsNone(query.access_type)
        self.assertFalse(w.should_show_clear())

        w.public_radio.click()
        self.assertEqual(len(spy), 1)
        self.assertTrue(w.should_show_clear())
        query.access_type = None
        w.apply_constraints_to_query(query)
        self.assertEqual(query.access_type, AccessType.Public)

        # reapply same, should be no signal
        w.set_from_query(query)
        self.assertEqual(len(spy), 1)

        w.private_radio.click()
        self.assertEqual(len(spy), 2)
        self.assertTrue(w.should_show_clear())
        query.access_type = None
        w.apply_constraints_to_query(query)
        self.assertEqual(query.access_type, AccessType.Private)
        w.set_from_query(query)
        self.assertEqual(len(spy), 2)

        # clear using query params
        # this should never raise signals
        query.access_type = None
        w.set_from_query(query)
        self.assertEqual(len(spy), 2)
        query.access_type = AccessType.Private
        w.apply_constraints_to_query(query)
        self.assertIsNone(query.access_type)

        # clear using clear button
        query.access_type = AccessType.Private
        w.set_from_query(query)
        self.assertEqual(len(spy), 2)
        self.assertTrue(w.should_show_clear())
        w.clear()
        self.assertEqual(len(spy), 3)
        self.assertFalse(w.should_show_clear())
        w.apply_constraints_to_query(query)
        self.assertIsNone(query.access_type)
        w.clear()
        self.assertEqual(len(spy), 3)

    def test_group_widget(self):
        w = GroupFilterWidget()

        # should start cleared
        self.assertFalse(w.should_show_clear())
        query = DataBrowserQuery()
        self.assertIsNone(query.group)
        w.apply_constraints_to_query(query)
        self.assertIsNone(query.group)

        spy = QSignalSpy(w.changed)
        # re-clearing already cleared should not emit signals
        w.clear()
        self.assertEqual(len(spy), 0)
        self.assertFalse(w.should_show_clear())

        # apply same query to widget, should be no signals
        w.set_from_query(query)
        self.assertEqual(len(spy), 0)
        w.apply_constraints_to_query(query)
        self.assertIsNone(query.group)
        self.assertFalse(w.should_show_clear())

        # set facets to build buttons
        w.set_facets({
            'group': [
                {'name': 'Transport', 'key': 'transport'},
                {'name': 'Water', 'key': 'water'},
                {'name': 'Environment', 'key': 'enviro'},
            ],
            'from': 'my_org'
        })

        w._radios[0].click()
        self.assertEqual(len(spy), 1)
        self.assertTrue(w.should_show_clear())
        query.group = None
        w.apply_constraints_to_query(query)
        self.assertEqual(query.group, 'transport')

        # reapply same, should be no signal
        w.set_from_query(query)
        self.assertEqual(len(spy), 1)

        w._radios[1].click()
        self.assertEqual(len(spy), 2)
        self.assertTrue(w.should_show_clear())
        query.group = None
        w.apply_constraints_to_query(query)
        self.assertEqual(query.group, 'water')
        w.set_from_query(query)
        self.assertEqual(len(spy), 2)

        # clear using query params
        # this should never raise signals
        query.group = None
        w.set_from_query(query)
        self.assertEqual(len(spy), 2)
        query.group = 'water'
        w.apply_constraints_to_query(query)
        self.assertIsNone(query.group)

        # clear using clear button
        w._radios[0].click()
        self.assertEqual(len(spy), 3)
        self.assertTrue(w.should_show_clear())
        w.clear()
        self.assertEqual(len(spy), 4)
        self.assertFalse(w.should_show_clear())
        w.apply_constraints_to_query(query)
        self.assertIsNone(query.group)

        w.clear()
        self.assertEqual(len(spy), 4)

        w._radios[0].click()
        self.assertEqual(len(spy), 5)
        # reapply same facet -- should not change setting, or raise signal
        w.set_facets({
            'group': [
                {'name': 'Transport', 'key': 'transport'},
                {'name': 'Water', 'key': 'water'},
                {'name': 'Environment', 'key': 'enviro'},
            ],
            'from': 'my_org'
        })
        self.assertEqual(len(spy), 5)
        query.group = None
        w.apply_constraints_to_query(query)
        self.assertEqual(query.group, 'transport')

    def test_date_widget(self):
        w = DateFilterWidget()

        # should start cleared
        self.assertFalse(w.should_show_clear())
        query = DataBrowserQuery()
        self.assertIsNone(query.created_minimum)
        self.assertIsNone(query.created_maximum)
        self.assertIsNone(query.updated_minimum)
        self.assertIsNone(query.updated_maximum)
        w.apply_constraints_to_query(query)
        self.assertIsNone(query.created_minimum)
        self.assertIsNone(query.created_maximum)
        self.assertIsNone(query.updated_minimum)
        self.assertIsNone(query.updated_maximum)

        spy = QSignalSpy(w.changed)
        # re-clearing already cleared should not emit signals
        w.clear()
        self.assertEqual(len(spy), 0)
        self.assertFalse(w.should_show_clear())

        # apply same query to widget, should be no signals
        w.set_from_query(query)
        self.assertEqual(len(spy), 0)
        w.apply_constraints_to_query(query)
        self.assertIsNone(query.created_minimum)
        self.assertIsNone(query.created_maximum)
        self.assertIsNone(query.updated_minimum)
        self.assertIsNone(query.updated_maximum)
        self.assertFalse(w.should_show_clear())

        # set facets to ranges
        w.set_facets({
            'updated_at': {
                'min': '2022-01-01T00:00',
                'max': '2022-05-01T00:00'},
            'created_at': {
                'min': '2021-01-01T00:00',
                'max': '2021-05-01T00:00'},
        })

        w.min_updated_date_edit.setDate(QDate(2022,3,4))
        self.assertEqual(len(spy), 1)
        self.assertTrue(w.should_show_clear())
        query.updated_minimum = None
        w.apply_constraints_to_query(query)
        self.assertEqual(query.updated_minimum, QDateTime(2022,3,4,0,0))

        # reapply same, should be no signal
        w.min_updated_date_edit.setDate(QDate(2022,3,4))
        self.assertEqual(len(spy), 1)
        w.set_from_query(query)
        self.assertEqual(len(spy), 1)

        w.max_updated_date_edit.setDate(QDate(2022,3,6))
        self.assertEqual(len(spy), 2)
        self.assertTrue(w.should_show_clear())
        query.updated_maximum = None
        w.apply_constraints_to_query(query)
        self.assertEqual(query.updated_minimum, QDateTime(2022,3,4,0,0))
        self.assertEqual(query.updated_maximum, QDateTime(2022,3,6,0,0))
        w.set_from_query(query)
        self.assertEqual(len(spy), 2)

        # clear using query params
        # this should never raise signals
        query.updated_minimum = None
        query.updated_maximum = None
        w.set_from_query(query)
        self.assertEqual(len(spy), 2)
        w.apply_constraints_to_query(query)
        self.assertIsNone(query.created_minimum)
        self.assertIsNone(query.created_maximum)
        self.assertIsNone(query.updated_minimum)
        self.assertIsNone(query.updated_maximum)
        query.updated_minimum = QDateTime(2022,2,4,0,0)
        query.updated_maximum = QDateTime(2022, 2, 6, 0, 0)
        w.apply_constraints_to_query(query)
        self.assertIsNone(query.created_minimum)
        self.assertIsNone(query.created_maximum)
        self.assertIsNone(query.updated_minimum)
        self.assertIsNone(query.updated_maximum)

        # clear using clear button
        w.max_updated_date_edit.setDate(QDate(2022,3,6))
        self.assertEqual(len(spy), 3)
        self.assertTrue(w.should_show_clear())
        w.clear()
        self.assertEqual(len(spy), 4)
        self.assertFalse(w.should_show_clear())
        w.apply_constraints_to_query(query)
        self.assertIsNone(query.created_minimum)
        self.assertIsNone(query.created_maximum)
        self.assertIsNone(query.updated_minimum)
        self.assertIsNone(query.updated_maximum)

        w.clear()
        self.assertEqual(len(spy), 4)

        w.max_updated_date_edit.setDate(QDate(2022, 3, 6))
        self.assertEqual(len(spy), 5)
        # reapply same facet -- should not change setting, or raise signal
        w.set_facets({
            'updated_at': {
                'min': '2022-01-01T00:00',
                'max': '2022-05-01T00:00'},
            'created_at': {
                'min': '2021-01-01T00:00',
                'max': '2021-05-01T00:00'},
        })
        self.assertEqual(len(spy), 5)
        query.updated_minimum = None
        query.updated_maximum = None
        w.apply_constraints_to_query(query)
        self.assertIsNone(query.created_minimum)
        self.assertIsNone(query.created_maximum)
        self.assertIsNone(query.updated_minimum)
        self.assertEqual(query.updated_maximum, QDateTime(2022,3,6,0,0))

    def test_license_widget(self):
        w = LicenseFilterWidget()

        # should start cleared
        self.assertFalse(w.should_show_clear())
        query = DataBrowserQuery()
        self.assertFalse(query.cc_license_versions)
        self.assertFalse(query.cc_license_allow_derivates)
        self.assertFalse(query.cc_license_allow_commercial)
        self.assertFalse(query.cc_license_changes_must_be_shared)
        w.apply_constraints_to_query(query)
        self.assertFalse(query.cc_license_versions)
        self.assertFalse(query.cc_license_allow_derivates)
        self.assertFalse(query.cc_license_allow_commercial)
        self.assertFalse(query.cc_license_changes_must_be_shared)

        spy = QSignalSpy(w.changed)
        # re-clearing already cleared should not emit signals
        w.clear()
        self.assertEqual(len(spy), 0)
        self.assertFalse(w.should_show_clear())

        # apply same query to widget, should be no signals
        w.set_from_query(query)
        self.assertEqual(len(spy), 0)
        w.apply_constraints_to_query(query)
        self.assertFalse(query.cc_license_versions)
        self.assertFalse(query.cc_license_allow_derivates)
        self.assertFalse(query.cc_license_allow_commercial)
        self.assertFalse(query.cc_license_changes_must_be_shared)
        self.assertFalse(w.should_show_clear())

        w.cc_3_checkbox.setChecked(True)
        self.assertEqual(len(spy), 1)
        self.assertTrue(w.should_show_clear())
        query.cc_license_versions = set()
        query.cc_license_allow_derivates = False
        query.cc_license_allow_commercial = False
        query.cc_license_changes_must_be_shared = False
        w.apply_constraints_to_query(query)
        self.assertEqual(query.cc_license_versions, {
            CreativeCommonLicenseVersions.Version3
        })
        self.assertFalse(query.cc_license_allow_derivates)
        self.assertFalse(query.cc_license_allow_commercial)
        self.assertFalse(query.cc_license_changes_must_be_shared)

        # reapply same, should be no signal
        w.set_from_query(query)
        self.assertEqual(len(spy), 1)

        w.cc_4_checkbox.setChecked(True)
        self.assertEqual(len(spy), 2)
        self.assertTrue(w.should_show_clear())
        query.cc_license_versions = set()
        query.cc_license_allow_derivates = False
        query.cc_license_allow_commercial = False
        query.cc_license_changes_must_be_shared = False
        w.apply_constraints_to_query(query)
        self.assertEqual(query.cc_license_versions, {
            CreativeCommonLicenseVersions.Version3,
            CreativeCommonLicenseVersions.Version4
        })
        self.assertFalse(query.cc_license_allow_derivates)
        self.assertFalse(query.cc_license_allow_commercial)
        self.assertFalse(query.cc_license_changes_must_be_shared)
        w.set_from_query(query)
        self.assertEqual(len(spy), 2)

        # clear using query params
        # this should never raise signals
        query.cc_license_versions = set()
        query.cc_license_allow_derivates = False
        query.cc_license_allow_commercial = False
        query.cc_license_changes_must_be_shared = False
        w.set_from_query(query)
        self.assertEqual(len(spy), 2)
        query.cc_license_versions = {
            CreativeCommonLicenseVersions.Version3
        }
        w.apply_constraints_to_query(query)
        self.assertFalse(query.cc_license_versions)

        # clear using clear button
        w.cc_4_checkbox.setChecked(True)
        self.assertEqual(len(spy), 3)
        self.assertTrue(w.should_show_clear())
        w.clear()
        self.assertEqual(len(spy), 4)
        self.assertFalse(w.should_show_clear())
        w.apply_constraints_to_query(query)
        self.assertFalse(query.cc_license_versions)
        self.assertFalse(query.cc_license_allow_derivates)
        self.assertFalse(query.cc_license_allow_commercial)
        self.assertFalse(query.cc_license_changes_must_be_shared)

        w.clear()
        self.assertEqual(len(spy), 4)

        # try options
        w.cc_3_checkbox.setChecked(True)
        self.assertEqual(len(spy), 5)
        w.derivatives_allowed_radio.click()
        self.assertEqual(len(spy), 6)
        w.apply_constraints_to_query(query)
        self.assertEqual(query.cc_license_versions, {
            CreativeCommonLicenseVersions.Version3
        })
        self.assertTrue(query.cc_license_allow_derivates)
        w.set_from_query(query)
        self.assertEqual(len(spy), 6)
        w.clear()
        self.assertEqual(len(spy), 7)

    def test_publisher_widget(self):
        w = PublisherFilterWidget()

        # should start cleared
        self.assertFalse(w.should_show_clear())
        query = DataBrowserQuery()
        self.assertIsNone(query.publisher)
        w.apply_constraints_to_query(query)
        self.assertIsNone(query.publisher)

        spy = QSignalSpy(w.changed)
        # re-clearing already cleared should not emit signals
        w.clear()
        self.assertEqual(len(spy), 0)
        self.assertFalse(w.should_show_clear())

        # apply same query to widget, should be no signals
        w.set_from_query(query)
        self.assertEqual(len(spy), 0)
        w.apply_constraints_to_query(query)
        self.assertIsNone(query.publisher)
        self.assertFalse(w.should_show_clear())

        publisher1 = Publisher({
            'id': 'site:1'
        })
        publisher2 = Publisher({
            'id': 'site:2'
        })
        w._selection_changed(publisher1)

        self.assertEqual(len(spy), 1)
        self.assertTrue(w.should_show_clear())
        query.publisher = None
        w.apply_constraints_to_query(query)
        self.assertEqual(query.publisher.id(), 'site:1')

        # reapply same, should be no signal
        w.set_from_query(query)
        self.assertEqual(len(spy), 1)

        w._selection_changed(publisher1)
        self.assertEqual(len(spy), 1)

        w._selection_changed(publisher2)
        self.assertEqual(len(spy), 2)
        self.assertTrue(w.should_show_clear())
        query.publisher = None
        w.apply_constraints_to_query(query)
        self.assertEqual(query.publisher.id(), 'site:2')
        w.set_from_query(query)
        self.assertEqual(len(spy), 2)

        # clear using query params
        # this should never raise signals
        query.publisher = None
        w.set_from_query(query)
        self.assertEqual(len(spy), 2)
        query.publisher = publisher1
        w.apply_constraints_to_query(query)
        self.assertIsNone(query.publisher)

        # clear using clear button
        w._selection_changed(publisher2)
        self.assertEqual(len(spy), 3)
        self.assertTrue(w.should_show_clear())
        w.clear()
        self.assertEqual(len(spy), 4)
        self.assertFalse(w.should_show_clear())
        w.apply_constraints_to_query(query)
        self.assertIsNone(query.publisher)

        w.clear()
        self.assertEqual(len(spy), 4)

        w._selection_changed(publisher1)
        self.assertEqual(len(spy), 5)
        w._selection_changed(publisher1)
        self.assertEqual(len(spy), 5)
        query.publisher = None
        w.apply_constraints_to_query(query)
        self.assertEqual(query.publisher.id(), 'site:1')


if __name__ == '__main__':
    unittest.main()
