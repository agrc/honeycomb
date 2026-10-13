#!/usr/bin/env python
# * coding: utf8 *
"""
Tests for the honeycomb command-line entry point.
"""

from mock import call, patch

from honeycomb import __main__


def test_explode_job_updates_current_job_after_success():
    with (
        patch("honeycomb.__main__.start_new_job") as start_new_job,
        patch("honeycomb.__main__.update_job") as update_job,
        patch("honeycomb.__main__.explode_cache") as explode_cache,
        patch("honeycomb.__main__.finish_job") as finish_job,
    ):
        __main__.explode_job("Terrain")

    start_new_job.assert_called_once_with("Terrain", True, True, True, None, None)
    explode_cache.assert_called_once()
    update_job.assert_has_calls(
        [call("caching_complete", True), call("exploding_complete", True)]
    )
    finish_job.assert_called_once_with()


@patch("honeycomb.__main__.explode_job")
@patch("honeycomb.__main__.update_job")
@patch("honeycomb.__main__.send_email")
@patch(
    "honeycomb.__main__.get_current_job",
    return_value={"cache_args": ["Terrain"], "caching_complete": True},
)
@patch(
    "honeycomb.__main__.get_job_status",
    side_effect=lambda prop: prop == "caching_complete",
)
@patch("honeycomb.__main__.docopt")
def test_resume_restarts_incomplete_explode_job(
    docopt, get_job_status, get_current_job, send_email, update_job, explode_job
):
    docopt.return_value = {
        "config": False,
        "update-data": False,
        "upload": False,
        "loop": False,
        "vector": False,
        "vector-all": False,
        "cleanup": False,
        "explode": False,
        "<basemap>": None,
        "stats": False,
        "resume": True,
    }

    __main__.main()

    explode_job.assert_called_once_with("Terrain", is_resumed_job=True)
