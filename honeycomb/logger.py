'''
logger.py

A module for writing entries to StackDriver logging
'''

from google.cloud import logging

client = logging.Client()
logger = client.logger('honeycomb')


def _log(message, severity):
    logger.log_text(message, severity=severity)
    print('{}: {}'.format(severity, message))


def info(message):
    _log(message, 'INFO')


def error(message):
    _log(message, 'ERROR')


def warn(message):
    _log(message, 'WARNING')
