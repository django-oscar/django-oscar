import logging

from django.core.management.base import BaseCommand
from django.utils.translation import gettext_lazy as _

from oscar.apps.customer.alerts import utils

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    """
    Check stock records of products for availability and send out alerts
    to customers that have registered for an alert.
    """
    help = _("Check for products that are back in "
             "stock and send out alerts")

    def handle(self, **options):
        """
        Check all products with active product alerts for
        availability and send out email alerts when a product is
        available to buy.
        """
        utils.send_alerts()
