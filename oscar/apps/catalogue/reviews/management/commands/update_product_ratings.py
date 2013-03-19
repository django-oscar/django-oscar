# -*- coding: utf-8 -*-

from django.core.management.base import BaseCommand, CommandError
from django.db.models import get_model

Product = get_model('catalogue', 'Product')
ProductReview = get_model('reviews', 'ProductReview')


class Command(BaseCommand):
    help = """Update the denormalised reviews average on all Product instances.
              Should only be necessary when changing to e.g. a weight-based
              rating."""

    def handle(self, *args, **options):
        # go through all Products (not just ones with reviews)
        products = Product.objects.all()
        for product in products:
            ProductReview.update_product_rating(product)

        self.stdout.write('Successfully updated %s products\n'
                          % products.count())
