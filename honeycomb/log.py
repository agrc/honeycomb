import google.cloud.logging
import logging

logging.basicConfig(format="%(levelname)-7s %(asctime)s %(module)10s:%(lineno)5s %(message)s", datefmt="%m-%d %H:%M:%S")
logger = logging.getLogger("honeycomb")


def init():
    logger.setLevel(logging.INFO)
    client = google.cloud.logging.Client()
    client.setup_logging()
