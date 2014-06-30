from django.core.management.base import CommandError

from oscar.core.loading import get_class
from oscar.management import base

Calculator = get_class('analytics.scores', 'Calculator')


class Command(base.OscarBaseCommand):
    help = 'Calculate product scores based on analytics data'

    def run(self, *args, **options):
        Calculator(self.logger).run()
