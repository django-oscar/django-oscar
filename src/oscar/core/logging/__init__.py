import logging
import os

from django.conf import settings


def get_file_logger(filename, level=logging.INFO):
    """
    Return a logger that uses a file handler for the given filename but in the
    LOG_ROOT.
    """
    filepath = os.path.join(settings.LOG_ROOT, filename)
    handler = logging.FileHandler(filepath)
    handler.setLevel(level)
    logger = logging.getLogger(filepath)
    logger.addHandler(handler)
    logger.setLevel(level)
    return logger
