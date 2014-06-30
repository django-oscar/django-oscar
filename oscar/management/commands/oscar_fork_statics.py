import os

from oscar.core import customisation
from oscar.management import base


class Command(base.OscarBaseCommand):
    args = '<destination folder>'
    help = (
        "Copy Oscar's static files to a given destination so they can be "
        "used as a base for styling a new site")

    def run(self, *args, **options):
        # Determine where to copy to
        folder = args[0] if args else 'static'
        if not folder.startswith('/'):
            destination = os.path.join(os.getcwd(), folder)
        else:
            destination = folder
        customisation.fork_statics(destination, logger=self.logger)
