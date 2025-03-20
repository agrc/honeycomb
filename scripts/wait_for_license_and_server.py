import logging
from time import sleep

import google.cloud.logging
import requests

logging.basicConfig(
    format="%(levelname)-7s %(asctime)s %(module)10s:%(lineno)5s %(message)s",
    datefmt="%m-%d %H:%M:%S",
)
logger = logging.getLogger("honeycomb")
logger.setLevel(logging.INFO)
client = google.cloud.logging.Client()
client.setup_logging()

tries = 0
while True:
    try:
        import arcpy  # noqa: F401

        logger.info("license found")

        break
    except:  # noqa: E722
        logger.info("no license available, waiting...")

        if tries > 50:
            logger.error(Exception("no arcpy license available!"))
        tries += 1
        sleep(10)

tries = 0
while True:
    try:
        requests.get("https://localhost:6443/arcgis/rest/", verify=False)

        logger.info("arcgis server has started")

        break
    except:  # noqa: E722
        logger.info("waiting for arcgis server to start")

        if tries > 100:
            logger.error(Exception("arcgis server did not start!"))

        tries += 1
        sleep(10)

logger.info("waiting for 5 minutes for anything else that needs to spin up")
sleep(60 * 5)
