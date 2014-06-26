import logging
import os

from django.core.management.base import BaseCommand, CommandError

from oscar.core import customisation


logger = logging.getLogger(__name__)


class Command(BaseCommand):
    """
    Copy Oscar's statics into the local project so they can be used as a base
    for styling a new site.
    """
    args = '<destination folder>'
    help = "Copy Oscar's static files to a given destination"

    def handle(self, *args, **options):
        # Determine where to copy to
        folder = args[0] if args else 'static'
        if not folder.startswith('/'):
            destination = os.path.join(os.getcwd(), folder)
        else:
            destination = folder

        # Use a stdout logger
        logger = logging.getLogger(__name__)
        stream = logging.StreamHandler(self.stdout)
        logger.addHandler(stream)
        logger.setLevel(logging.DEBUG)

        try:
            customisation.fork_statics(destination, logger=logger)
        except Exception, e:
            raise CommandError(e.message)
