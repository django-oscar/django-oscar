from django.db import connection, transaction
from oscar.core.loading import get_model

ProductRecord = get_model('analytics', 'ProductRecord')
Product = get_model('catalogue', 'Product')


class Calculator(object):

    # Map of field name to weight
    weights = {'num_views': 1,
               'num_basket_additions': 3,
               'num_purchases': 5}

    def __init__(self, logger):
        self.logger = logger
        self.cursor = connection.cursor()

    def run(self):
        self.calculate_scores()
        self.update_product_models()

    def calculate_scores(self):
        self.logger.info("Calculating product scores")

        # Build the "SET ..." part of the SQL statement
        weighted_sum = " + ".join(
            ['%s*"%s"' % (weight, field) for field, weight
             in self.weights.items()])

        ctx = {'table': ProductRecord._meta.db_table,
               'weighted_total': weighted_sum,
               'total_weight': sum(self.weights.values())}
        sql = '''UPDATE "%(table)s"
                 SET score = %(weighted_total)s / %(total_weight)s''' % ctx

        self.logger.debug(sql)
        self.cursor.execute(sql)
        transaction.commit_unless_managed()

    def update_product_models(self):
        self.logger.info("Updating product records")
        qs = ProductRecord.objects.all()
        for record in qs:
            record.product.score = record.score
            record.product.save()
        self.logger.info("Updated scores for %d products" % qs.count())
