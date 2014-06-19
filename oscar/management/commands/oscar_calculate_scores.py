import logging

from django.core.management.base import NoArgsCommand

from oscar.core.loading import get_class
Calculator = get_class('analytics.scores', 'Calculator')

logger = logging.getLogger(__name__)


class Command(NoArgsCommand):
    help = 'Calculate product scores based on analytics data'

    def handle_noargs(self, **options):
        Calculator(logger).run()
