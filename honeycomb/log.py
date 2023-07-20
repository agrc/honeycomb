import logging

import google.cloud.logging
from tqdm import tqdm

logging.basicConfig(format="%(levelname)-7s %(asctime)s %(module)10s:%(lineno)5s %(message)s", datefmt="%m-%d %H:%M:%S")
logger = logging.getLogger("honeycomb")


def init():
    logger.setLevel(logging.INFO)
    client = google.cloud.logging.Client()
    client.setup_logging()


#: https://github.com/tqdm/tqdm/issues/313#issuecomment-812224667
class logging_tqdm(tqdm):
    def __init__(self, *args, **kwargs):
        self._logger = logger
        self._last_log_n = -1
        ncols = 80
        mininterval = 60 * 5  #: seconds
        super().__init__(*args, mininterval=mininterval, ncols=ncols, **kwargs)

    @property
    def logger(self):
        return logger

    def display(self, msg=None, pos=None):
        if not self.n:
            # skip progress bar before having processed anything
            return
        if self.n == self._last_log_n:
            # avoid logging for the same progress multiple times
            return
        self._last_log_n = self.n
        if msg is None:
            msg = self.__str__()
        if not msg:
            return

        self.logger.info("%s", msg)
