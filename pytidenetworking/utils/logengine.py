import logging
from logging import Logger
import sys

from typing import Dict, Optional

LOG_FORMAT = '[%(asctime)s] [%(levelname)s] %(message)s at %(pathname)s, line %(lineno)d, Function: %(funcName)s'
LOG_TO_CONSOLE = True
LOG_TO_FILE = False
LOG_FILE = "pytide.log"

LOG_LEVEL = logging.DEBUG


def getLogger(name=None, level=None, isVerbose=False) -> Logger:
    """
    Prepares a logger & returns the resulting logger

    :param name:
    :param level:
    :param isVerbose:
    :return: the logger set up
    """
    if level is None:
        if isVerbose:
            log_level = logging.DEBUG
        else:
            log_level = LOG_LEVEL
    else:
        log_level = level

    log_format = logging.Formatter(LOG_FORMAT)
    log = logging.getLogger(name)
    log.setLevel(log_level)

    if not log.hasHandlers():
        if LOG_TO_FILE:
            # Writing to log file
            handler = logging.FileHandler(LOG_FILE)
            handler.setLevel(log_level)
            handler.setFormatter(log_format)
            log.addHandler(handler)

        if LOG_TO_CONSOLE:
            # writing to stdout
            handler = logging.StreamHandler(sys.stdout)
            handler.setLevel(log_level)
            handler.setFormatter(log_format)
            log.addHandler(handler)

    return log