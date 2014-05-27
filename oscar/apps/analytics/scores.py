from django.db.models import F
from oscar.core.loading import get_model

ProductRecord = get_model('analytics', 'ProductRecord')
Product = get_model('catalogue', 'Product')


class Calculator(object):

    # Map of field name to weight
    weights = {
        'num_views': 1,
        'num_basket_additions': 3,
        'num_purchases': 5
    }

    def __init__(self, logger):
        self.logger = logger

    def run(self):
        self.calculate_scores()
        self.update_product_models()

    def calculate_scores(self):
        self.logger.info("Calculating product scores")
        total_weight = float(sum(self.weights.values()))
        weighted_fields = [
            self.weights[name] * F(name) for name in self.weights.keys()]
        ProductRecord.objects.update(
            score=sum(weighted_fields)/total_weight)

    def update_product_models(self):
        self.logger.info("Updating product records")
        records = ProductRecord.objects.select_related('product')
        for record in records:
            record.product.score = record.score
            record.product.save()
        self.logger.info("Updated scores for %d products" % len(records))
