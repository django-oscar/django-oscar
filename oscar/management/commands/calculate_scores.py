import logging

from django.core.management.base import BaseCommand

from oscar.core.loading import import_module
import_module('analytics.utils', ['ScoreCalculator'], locals())


class Command(BaseCommand):
    
    help = 'Calculate product scores based on analytics data'
    
    def handle(self, *args, **options):
        
        logger = logging.getLogger(__name__)
        calculator = ScoreCalculator(logger)
        calculator.run()

        
        
        
            