#!/usr/bin/env python
# * coding: utf8 *
"""
test_worker_bee.py

A module that contains tests for the cache module.
"""

from honeycomb.worker_bee import WorkerBee, intersect_scales, parse_levels
from mock import Mock, call, patch


@patch("honeycomb.worker_bee.socket.gethostbyname", return_value="")
@patch("honeycomb.worker_bee.WorkerBee.cache")
@patch("honeycomb.worker_bee.WorkerBee.cache_test_extent")
@patch("honeycomb.worker_bee.WorkerBee.get_bundles_count")
def test_init(get_bundles_count, cache_test_extent, cache, host_mock):
    WorkerBee("Terrain", skip_update=True)

    get_bundles_count.assert_called_once()
    cache_test_extent.assert_called_once()


@patch("__builtin__.raw_input", return_value="F")
@patch("honeycomb.worker_bee.WorkerBee.get_bundles_count")
@patch("honeycomb.worker_bee.socket.gethostbyname", return_value="")
@patch("honeycomb.update_data.main")
def test_cache_extent(update_mock, host_mock, count_mock, input_mock):
    WorkerBee("Terrain", spot_path="blah")


def test_spot_cache_recaches_errors_before_exploding():
    manager = Mock()

    with patch("honeycomb.worker_bee.config.get_basemap") as get_basemap, patch(
        "honeycomb.worker_bee.config.is_dev", return_value=True
    ), patch("honeycomb.worker_bee.utilities.validate_map_layers"), patch(
        "honeycomb.worker_bee.update_job"
    ), patch(
        "honeycomb.worker_bee.WorkerBee.delete_cache"
    ), patch(
        "honeycomb.worker_bee.WorkerBee.get_bundles_count", return_value=0
    ), patch(
        "honeycomb.worker_bee.WorkerBee.cache_extent"
    ) as cache_extent, patch(
        "honeycomb.worker_bee.WorkerBee.recache_errors"
    ) as recache_errors, patch(
        "honeycomb.worker_bee.explode_cache"
    ) as explode_cache, patch(
        "honeycomb.worker_bee.arcpy.analysis.Intersect", return_value="intersected"
    ):
        get_basemap.return_value = {"imageType": "jpeg"}
        manager.attach_mock(recache_errors, "recache_errors")
        manager.attach_mock(explode_cache, "explode_cache")

        WorkerBee("Terrain", skip_update=True, skip_test=True, spot_path="blah")

    assert cache_extent.call_count == 2
    assert manager.mock_calls == [
        call.recache_errors(),
        call.explode_cache("Terrain"),
    ]


def test_recache_errors_retries_until_empty():
    bee = WorkerBee.__new__(WorkerBee)
    bee.errors = [
        [[1], "first aoi", "first name"],
        [[2], "second aoi", "second name"],
    ]
    bee.cache_extent = Mock()

    bee.recache_errors()

    assert bee.errors == []
    bee.cache_extent.assert_has_calls(
        [
            call([2], "second aoi", "second name"),
            call([1], "first aoi", "first name"),
        ]
    )


@patch("honeycomb.worker_bee.socket.gethostbyname", return_value="")
@patch("honeycomb.worker_bee.WorkerBee.cache")
@patch("honeycomb.worker_bee.WorkerBee.get_bundles_count", return_value=0)
def test_get_progress(get_bundles_count, cache, host_mock):
    bee = WorkerBee("Terrain", skip_update=True, skip_test=True)

    assert (
        bee.get_progress()
        == "0 of 19 (0%) bundle files created.\nEstimated hours remaining: ??"
    )


def test_parse_levels():
    assert parse_levels("5-7") == [1.8489297737236e7, 9244648.868618, 4622324.434309]


def test_intersect_scales():
    assert intersect_scales([1, 2, 4], [1, 2, 3]) == [1, 2]
