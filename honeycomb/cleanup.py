from pathlib import Path
from shutil import rmtree

from . import config, settings
from .log import logger


def main():
    logger.info("cleaning up current job data...")
    file_path = Path(config.config_folder) / "current_job.json"
    file_path.unlink(missing_ok=True)

    basemaps = config.get_config_value("basemaps")
    for basemap in [key for key in list(basemaps.keys())]:
        logger.info(f"cleaning up {basemap} tiles...")
        folder = Path(settings.CACHES_DIR) / basemap / basemap / "_alllayers"
        if folder.exists():
            #: loop through all child folders
            for level_folder in folder.iterdir():
                logger.info(f"deleting {level_folder}...")
                rmtree(level_folder)
