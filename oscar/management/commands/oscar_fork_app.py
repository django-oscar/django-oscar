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
        super(Command, self).handle(*args, **options)

    def run(self, *args, **options):
        app_label, folder_path = args[:2]
        customisation.fork_app(
            app_label, folder_path, self.logger)
