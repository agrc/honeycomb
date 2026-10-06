from pathlib import Path
from unittest.mock import patch

from honeycomb import settings, utilities


@patch("honeycomb.utilities.config.get_basemap")
def test_get_cache_directory_uses_configured_location(mock_get_basemap):
    mock_get_basemap.return_value = {"cacheLocation": r"C:\Cache\Outdoors"}

    assert utilities.get_cache_directory("Outdoors") == Path(r"C:\Cache\Outdoors")


@patch("honeycomb.utilities.config.get_basemap")
@patch("honeycomb.utilities.logger.warning")
def test_get_cache_directory_uses_default_when_config_is_missing(
    mock_warning, mock_get_basemap
):
    mock_get_basemap.side_effect = KeyError("Outdoors")

    assert utilities.get_cache_directory("Outdoors") == settings.CACHES_DIR
    mock_warning.assert_called_once()
