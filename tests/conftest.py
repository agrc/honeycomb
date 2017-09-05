from os import path
from os import remove
import pytest
import sys

#: mock arcpy
sys.path.insert(0, path.join(path.dirname(__file__), 'mocks'))
from honeycomb import config  # NOQA

config.config_location = path.join(path.abspath(path.dirname(__file__)), 'config.json')
config.ags_connection_file = path.join(path.abspath(path.dirname(__file__)), 'arcgisserver.ags')


def cleanup():
    for clean_file in [config.config_location, config.ags_connection_file]:
        if path.exists(clean_file):
            remove(clean_file)


@pytest.fixture(scope='function', autouse=True)
def setup_teardown():
    cleanup()
    yield
    cleanup()
