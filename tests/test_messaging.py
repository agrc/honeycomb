#!/usr/bin/env python
# * coding: utf8 *
"""
test_messaging.py

A module that contains tests for the messaging module.
"""

from mock import patch

from honeycomb import messaging


@patch("os.environ.get", return_value="blah")
@patch("honeycomb.config.get_config_value", return_value=False)
def test_send_email(config_mock, environ_mock):
    assert messaging.send_email("test sub", "test body")
