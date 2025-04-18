import logging
import sys
from os import linesep

import google.cloud.logging
from tqdm import tqdm

logging.basicConfig(
    format="%(levelname)-7s %(asctime)s %(module)10s:%(lineno)5s %(message)s",
    datefmt="%m-%d %H:%M:%S",
)
logger = logging.getLogger("honeycomb")
logger.setLevel(logging.INFO)
try:
    client = google.cloud.logging.Client()
    client.setup_logging()
except Exception:
    print("Could not setup google cloud logging. Logging to console only.")


def global_exception_handler(ex_cls, ex, tb):
    """
    ex_cls: Class - the type of the exception
    ex: object - the exception object
    tb: Traceback

    Used to handle any uncaught exceptions. Formats an error message and logs it.
    """
    import traceback

    last_traceback = (traceback.extract_tb(tb))[-1]
    line_number = last_traceback[1]
    file_name = last_traceback[0].split(".")[0]
    error = linesep.join(traceback.format_exception(ex_cls, ex, tb))

    logger.error(("global error handler line: %s (%s)" % (line_number, file_name)))
    logger.error(error)


#: add global exception handlers
sys.excepthook = global_exception_handler


#: https://github.com/tqdm/tqdm/issues/313#issuecomment-812224667
#: this makes tqdm logging more friendly to and show up in cloud logs
class logging_tqdm(tqdm):
    def __init__(self, *args, **kwargs):
        self._logger = logger
        self._last_log_n = -1
        ncols = 80
        super().__init__(*args, ncols=ncols, **kwargs)

    @property
    def logger(self):
        return logger

    def display(self, msg=None, pos=None):
        if self.n == self._last_log_n:
            # avoid logging for the same progress multiple times
            return
        self._last_log_n = self.n
        if msg is None:
            msg = self.__str__()
        if not msg:
            return

        self.logger.info("%s", msg)
