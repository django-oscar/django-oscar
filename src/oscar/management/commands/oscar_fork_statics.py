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
    help = "Copy Oscar's static files"

    def add_arguments(self, parser):
        parser.add_argument('target_path', nargs='?', default='static',
                            help='Directory path (relative to current working '
                                 'directory, or absolute) in local project, to '
                                 'copy files to. This directory should be '
                                 'included in STATICFILES_DIRS, in order for '
                                 'your local overrides to be picked up.')

    def handle(self, *args, **options):
        # Determine where to copy to
        folder = options['target_path']
        if not folder.startswith('/'):
            destination = os.path.join(os.getcwd(), folder)
        else:
            destination = folder
        if os.path.exists(destination):
            raise CommandError(
                "The folder %s already exists - aborting!" % destination)

        source = os.path.realpath(
            os.path.join(os.path.dirname(__file__), '../../static'))
        self.stdout.write("Copying Oscar's static files to %s" % destination)
        shutil.copytree(source, destination)

        # Check if this new folder is in STATICFILES_DIRS
        if destination not in settings.STATICFILES_DIRS:
            self.stdout.write("You need to add %s to STATICFILES_DIRS in order for your local overrides to be picked "
                              "up" % destination)
