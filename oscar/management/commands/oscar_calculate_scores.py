import logging

from django.core.management.base import BaseCommand

from oscar.core.loading import import_module
import_module('analytics.utils', ['ScoreCalculator'], locals())

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Calculate product scores based on analytics data'
    
    def handle(self, *args, **options):
        ScoreCalculator(logger).run()

        
        
        
            