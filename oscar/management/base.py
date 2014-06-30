import logging

from django.core.management.base import BaseCommand, CommandError


class OscarBaseCommand(BaseCommand):
    """
    A base command class to duplicated code to handle logging and exception
    handling.
    """
    logger_name = None

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

    def handle(self, *args, **options):
        self.logger = self.logger(
            self.logger_name or self.__class__.__module__)

        # We explicitly log the start and end of the command. This is very
        # useful audit information for cronjobs that can take a long time to
        # complete.

        # Only log interesting options
        log_options = dict([
            (k, v) for (k, v) in options.items() if k not in (
                'verbosity', 'settings', 'traceback', 'pythonpath')])
        cmd_name = self.__class__.__module__.split('.').pop()
        self.logger.debug("Running command %s with args %s and options %s",
                          cmd_name, args, log_options)
        try:
            self.run(*args, **options)
        except Exception as e:
            # IOError doesn't have a message
            message = e.message if e.message else unicode(e)
            self.logger.error(message, exc_info=True)
            raise CommandError(message)
        finally:
            self.logger.debug("Command %s finished", cmd_name)

    def run(self, *args, **options):
        raise NotImplemented()
