#!/usr/bin/env python
# * coding: utf8 *
"""
Tests for resumable job state.
"""

import json

from mock import patch

from honeycomb import resumable


def test_start_new_job_declines_to_overwrite_existing_job(tmp_path):
    job_path = tmp_path / "current_job.json"
    job_path.write_text('{"cache_args": ["Terrain"]}')

    with (
        patch.object(resumable, "file_path", job_path),
        patch("builtins.input", return_value="n") as input_mock,
    ):
        result = resumable.start_new_job("Lite", False, False, False, None, None)

    assert result is False
    assert json.loads(job_path.read_text()) == {"cache_args": ["Terrain"]}
    input_mock.assert_called_once()


def test_start_new_job_overwrites_existing_job_after_confirmation(tmp_path):
    job_path = tmp_path / "current_job.json"
    job_path.write_text('{"cache_args": ["Terrain"]}')

    with (
        patch.object(resumable, "file_path", job_path),
        patch("builtins.input", return_value="yes"),
    ):
        result = resumable.start_new_job("Lite", False, False, False, None, None)

    assert result is True
    assert json.loads(job_path.read_text())["cache_args"][0] == "Lite"
