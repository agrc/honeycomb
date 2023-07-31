import logging
from time import sleep

import google.cloud.logging
import requests

logging.basicConfig(format="%(levelname)-7s %(asctime)s %(module)10s:%(lineno)5s %(message)s", datefmt="%m-%d %H:%M:%S")
logger = logging.getLogger("honeycomb")
logger.setLevel(logging.INFO)
client = google.cloud.logging.Client()
client.setup_logging()

while True:
    try:
        import arcpy  # noqa: F401

        logger.info("license found")

        break
    except:  # noqa: E722
        logger.info("no license available, waiting...")
        sleep(10)

while True:
    try:
        requests.get("https://localhost:6443/arcgis/rest/", verify=False)

        logger.info("arcgis server has started")

        break
    except:  # noqa: E722
        logger.info("waiting for arcgis server to start")
        sleep(10)

logger.info("waiting for 5 minutes for anything else that needs to spin up")
sleep(60 * 5)
