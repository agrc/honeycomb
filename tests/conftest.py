import sys
from os import path, remove
from shutil import rmtree

import pytest

#: mock arcpy
sys.path.insert(0, path.join(path.dirname(__file__), "mocks"))
from honeycomb import config  # NOQA


config.config_location = path.join(path.abspath(path.dirname(__file__)), "config.json")
test_data_folder = path.join(path.dirname(__file__), "data")
temp_folder = path.join(test_data_folder, "temp")


def cleanup():
    for clean_path in [config.config_location, temp_folder]:
        if path.exists(clean_path):
            try:
                remove(clean_path)
            except Exception:
                rmtree(clean_path)


@pytest.fixture(scope="function", autouse=True)
def setup_teardown():
    cleanup()
    yield
    cleanup()
