#!/usr/bin/env python
# * coding: utf8 *
'''
test_worker_bee.py

A module that contains tests for the cache module.
'''

from honeycomb.worker_bee import WorkerBee
from mock import patch


@patch('honeycomb.worker_bee.WorkerBee.cache')
@patch('honeycomb.worker_bee.WorkerBee.cache_test_extent')
@patch('honeycomb.worker_bee.WorkerBee.get_bundles_count')
def test_init(get_bundles_count, cache_test_extent, cache):
    WorkerBee('Terrain', skip_update=True)

    get_bundles_count.assert_called_once()
    cache_test_extent.assert_called_once()