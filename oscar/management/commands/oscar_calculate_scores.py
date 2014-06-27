from django.core.management.base import CommandError

from oscar.core.loading import get_class
from oscar.management import base

Calculator = get_class('analytics.scores', 'Calculator')


class Command(base.OscarBaseCommand):
    help = 'Calculate product scores based on analytics data'

    def handle(self, *args, **options):
        logger = self.logger(__name__)
        try:
            Calculator(logger).run()
        except Exception, e:
            logger.error(e.message, exc_info=True)
            raise CommandError(e.message)
