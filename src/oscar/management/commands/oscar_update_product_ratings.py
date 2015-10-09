# -*- coding: utf-8 -*-

from django.core.management.base import BaseCommand

from oscar.core.loading import get_model

Product = get_model('catalogue', 'Product')


class Command(BaseCommand):
    help = """Update the denormalised reviews average on all Product instances.
              Should only be necessary when changing to e.g. a weight-based
              rating."""

    def handle(self, *args, **options):
        # Iterate over all Products (not just ones with reviews)
        products = Product.objects.all()
        for product in products:
            product.update_rating()
        self.stdout.write(
            'Successfully updated %s products\n' % products.count())
