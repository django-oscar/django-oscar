import logging

from django.core.management.base import BaseCommand


class OscarBaseCommand(BaseCommand):

    def logger(self, name):
        """
        Return a logger instance for the passed name

        This function adds a STDOUT stream handler if there are no handlers
        defined already for this name. It is conventional to call this method
        with the parameter `__name__`.
        """
        logger = logging.getLogger(name)
        if not logger.handlers:
            stream = logging.StreamHandler(self.stdout)
            logger.addHandler(stream)
            logger.setLevel(logging.DEBUG)
        return logger
