from os import path
from os import remove
from shutil import rmtree
import pytest
import sys


#: mock arcpy
sys.path.insert(0, path.join(path.dirname(__file__), 'mocks'))
from honeycomb import config  # NOQA


config.config_location = path.join(path.abspath(path.dirname(__file__)), 'config.json')
config.ags_connection_file = path.join(path.abspath(path.dirname(__file__)), 'arcgisserver.ags')
test_data_folder = path.join(path.dirname(__file__), 'data')
temp_folder = path.join(test_data_folder, 'temp')


def cleanup():
    for clean_path in [config.config_location, config.ags_connection_file, temp_folder]:
        if path.exists(clean_path):
            try:
                remove(clean_path)
            except:
                rmtree(clean_path)


@pytest.fixture(scope='function', autouse=True)
def setup_teardown():
    cleanup()
    yield
    cleanup()
