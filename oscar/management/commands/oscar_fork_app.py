import logging

from django.core.management.base import CommandError

from oscar.management import base
from oscar.core import customisation


class Command(base.OscarBaseCommand):
    args = '<app label> <destination folder>'
    help = (
        "Create a local version of one of Oscar's app so it can "
        "be customised")

    def handle(self, *args, **options):
        # Check that the app hasn't already been forked
        if len(args) < 2:
            raise CommandError(
                "You must specify an app label and a folder to create "
                "the new app in")

        logger = self.logger(__name__)
        app_label, folder_path = args[:2]
        try:
            customisation.fork_app(
                app_label, folder_path, logger)
        except Exception as e:
            # e.g. IOError doesn't have a message
            logger.error(e.message, exc_info=True)
            message = e.message if e.message else unicode(e)
            raise CommandError(message)
