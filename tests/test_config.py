#!/usr/bin/env python
# * coding: utf8 *
'''
test_config.py
A module that contains tests for config.py
'''
import arcpy

from honeycomb import config
from mock import patch
import pytest


def test_set_config_prop_overrides_default():
    assert config.set_config_prop('sendEmails', True)


@patch('honeycomb.config.create_default_config', wraps=config.create_default_config)
def test_get_config_creates_default_config(mock_obj):
    config._get_config()

    mock_obj.assert_called_once()


@patch('honeycomb.config._get_config')
def test_set_config_prop_raises_error_for_bad_property_names(mock_obj):
    with pytest.raises(ValueError):
        config.set_config_prop('this was', 'not found')


@patch('honeycomb.config._get_config')
def test_set_config_prop_appends_items_from_list_if_not_overriding(mock_obj):
    mock_obj.return_value = {'test': False, 'list': []}

    message = config.set_config_prop('list', [1, 2])

    assert message == 'Set list to [1, 2]'

    message = config.set_config_prop('test', True)

    assert message == 'Set test to True'


def test_add_basemap():
    config.add_basemap('Lite')
    message = config.add_basemap('Terrain')

    assert config._get_config()['basemaps'] == ['Lite', 'Terrain']
    assert message == 'Added "Terrain" basemap. Current basemaps: Lite, Terrain'


def test_remove_basemap():
    config.set_config_prop('basemaps', ['Lite', 'Terrain'])

    message = config.remove_basemap('Lite')

    assert config._get_config()['basemaps'] == ['Terrain']
    assert message == 'Removed "Lite" basemap. Current basemaps: Terrain'


def test_remove_invalid_basemap():
    assert config.remove_basemap('bad name') == '"bad name" is not a valid basemap name! Current basemaps: '


def test_get_config_value():
    assert not config.get_config_value('sendEmails')


def test_is_dev():
    config.set_config_prop('configuration', 'dev')

    assert config.is_dev()


@patch('arcpy.mapping.CreateGISServerConnectionFile', wraps=arcpy.mapping.CreateGISServerConnectionFile)
def test_get_ags_connection(mock):
    config.get_ags_connection()
    config.get_ags_connection()

    mock.assert_called_once()
