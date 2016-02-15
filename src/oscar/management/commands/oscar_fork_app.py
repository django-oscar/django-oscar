import logging

from django.core.management.base import BaseCommand, CommandError
from django.utils import six

from oscar.core import customisation


class Command(BaseCommand):
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

        # Use a stdout logger
        logger = logging.getLogger(__name__)
        stream = logging.StreamHandler(self.stdout)
        logger.addHandler(stream)
        logger.setLevel(logging.DEBUG)

        app_label, folder_path = args[:2]
        try:
            customisation.fork_app(app_label, folder_path, logger)
        except Exception as e:
            raise CommandError(six.text_type(e))
