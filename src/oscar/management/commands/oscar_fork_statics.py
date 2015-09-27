import logging
import os
import shutil

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    """
    Copy Oscar's statics into local project so they can be used as a base for
    styling a new site.
    """
    args = '<destination folder>'
    help = "Copy Oscar's static files"

    def handle(self, *args, **options):
        # Determine where to copy to
        folder = args[0] if args else 'static'
        if not folder.startswith('/'):
            destination = os.path.join(os.getcwd(), folder)
        else:
            destination = folder
        if os.path.exists(destination):
            raise CommandError(
                "The folder %s already exists - aborting!" % destination)

        source = os.path.realpath(
            os.path.join(os.path.dirname(__file__), '../../static'))
        print("Copying Oscar's static files to %s" % (destination,))
        shutil.copytree(source, destination)

        # Check if this new folder is in STATICFILES_DIRS
        if destination not in settings.STATICFILES_DIRS:
            print(("You need to add %s to STATICFILES_DIRS in order for your "
                   "local overrides to be picked up") % destination)
