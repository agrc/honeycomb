#!/usr/bin/env python
# * coding: utf8 *
'''
test_worker_bee.py

A module that contains tests for the cache module.
'''

from mock import patch

from honeycomb.worker_bee import WorkerBee


@patch('honeycomb.worker_bee.socket.gethostbyname', return_value='')
@patch('honeycomb.worker_bee.WorkerBee.cache')
@patch('honeycomb.worker_bee.WorkerBee.cache_test_extent')
@patch('honeycomb.worker_bee.WorkerBee.get_bundles_count')
def test_init(get_bundles_count, cache_test_extent, cache, host_mock):
    WorkerBee('Terrain', skip_update=True)

    get_bundles_count.assert_called_once()
    cache_test_extent.assert_called_once()


@patch('__builtin__.raw_input', return_value='F')
@patch('honeycomb.worker_bee.WorkerBee.get_bundles_count')
@patch('honeycomb.worker_bee.socket.gethostbyname', return_value='')
@patch('honeycomb.update_data.main')
def test_cache_extent(update_mock, host_mock, count_mock, input_mock):
    WorkerBee('Terrain', spot_path='blah')


@patch('honeycomb.worker_bee.socket.gethostbyname', return_value='')
@patch('honeycomb.worker_bee.WorkerBee.cache')
@patch('honeycomb.worker_bee.WorkerBee.get_bundles_count', return_value=0)
def test_get_progress(get_bundles_count, cache, host_mock):
    bee = WorkerBee('Terrain', skip_update=True, skip_test=True)

    assert bee.get_progress() == '0 of 19 (0%) bundle files created.\nEstimated hours remaining: ??'
