import os

from django.core.management.base import CommandError

from oscar.core import customisation
from oscar.management import base


class Command(base.OscarBaseCommand):
    args = '<destination folder>'
    help = (
        "Copy Oscar's static files to a given destination so they can be "
        "used as a base for styling a new site")

    def handle(self, *args, **options):
        # Determine where to copy to
        folder = args[0] if args else 'static'
        if not folder.startswith('/'):
            destination = os.path.join(os.getcwd(), folder)
        else:
            destination = folder

        logger = self.logger(__name__)
        try:
            customisation.fork_statics(destination, logger=logger)
        except Exception, e:
            logger.error(e.message, exc_info=True)
            raise CommandError(e.message)
