import logging

from django.core.management.base import BaseCommand, CommandError
from django.utils import six

from oscar.core import customisation


class Command(BaseCommand):
    args = '<app label> <destination folder>'
    help = (
        "Create a local version of one of Oscar's app so it can "
        "be customised")

    def add_arguments(self, parser):
        parser.add_argument('<app label>')
        parser.add_argument('<destination folder>')

    def handle(self, *args, **options):
        # Use a stdout logger
        logger = logging.getLogger(__name__)
        stream = logging.StreamHandler(self.stdout)
        logger.addHandler(stream)
        logger.setLevel(logging.DEBUG)

        app_label, folder_path = options['<app label>'], options['<destination folder>']
        try:
            customisation.fork_app(app_label, folder_path, logger)
        except Exception as e:
            raise CommandError(six.text_type(e))
