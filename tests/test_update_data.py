#!/usr/bin/env python
# * coding: utf8 *
"""
test_update_data.py

A module that contains tests for update_data.py
"""

from honeycomb import update_data


def test_get_sgid_lookup():
    lookup = update_data.get_SGID_lookup()

    assert lookup == {
        "CountyBoundaries": "SGID10.BOUNDARIES.CountyBoundaries",
        "Schools": "SGID10.LOCATION.Schools",
    }


def test_main_resets_workspace():
    import arcpy

    update_data.main()

    assert arcpy.env.workspace is None
