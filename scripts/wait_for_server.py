import logging
from time import sleep

import google.cloud.logging
import requests

logging.basicConfig()
google.cloud.logging.Client().setup_logging()

while True:
    try:
        requests.get("https://localhost:6443/arcgis/rest/", verify=False)

        logging.info("arcgis server has started")

        break
    except:  # noqa: E722
        logging.info("waiting for arcgis server to start")
        sleep(10)
