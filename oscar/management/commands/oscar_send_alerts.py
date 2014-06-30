from oscar.apps.customer.alerts import utils
from oscar.management import base


class Command(base.OscarBaseCommand):
    """
    Check stock records of products for availability and send out alerts
    to customers that have registered for an alert.
    """
    help = "Check for products that are back in stock and send out alerts"
    logger_name = 'oscar.alerts'

    def run(self, *args, **options):
        """
        Check all products with active product alerts for
        availability and send out email alerts when a product is
        available to buy.
        """
        utils.send_alerts(self.logger)
