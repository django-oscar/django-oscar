from oscar.core.loading import get_model
from oscar.management import base

Product = get_model('catalogue', 'Product')


class Command(base.OscarBaseCommand):
    help = """Update the denormalised reviews average on all Product instances.
              Should only be necessary when changing to e.g. a weight-based
              rating."""

    def run(self, *args, **options):
        # Iterate over all Products (not just ones with reviews)
        products = Product.objects.all()
        self.logger.info("Found %d products to update", products.count())
        for product in products:
            product.update_rating()
