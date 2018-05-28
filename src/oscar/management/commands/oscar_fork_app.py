import logging

from django.core.management.base import BaseCommand, CommandError

from oscar.core import customisation


class Command(BaseCommand):
    help = (
        "Create a local version of one of Oscar's app so it can "
        "be customised")

    def add_arguments(self, parser):
        parser.add_argument('app_label', help='The application to fork')
        parser.add_argument('target_path', help='The path to copy the files to')

    def handle(self, *args, **options):
        # Use a stdout logger
        logger = logging.getLogger(__name__)
        stream = logging.StreamHandler(self.stdout)
        logger.addHandler(stream)
        logger.setLevel(logging.DEBUG)

        app_label, folder_path = options['app_label'], options['target_path']
        try:
            customisation.fork_app(app_label, folder_path, logger)
        except Exception as e:
            raise CommandError(str(e))
