import logging
from time import sleep

import google.cloud.logging

logging.basicConfig()
google.cloud.logging.Client().setup_logging()

while True:
    try:
        import arcpy  # noqa: F401

        logging.info("license found")

        break
    except:  # noqa: E722
        logging.info("no license available, waiting...")
        sleep(10)
