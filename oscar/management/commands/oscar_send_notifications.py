import logging

from django.db.models import get_model
from django.utils.translation import ugettext_lazy as _
from django.core.management.base import NoArgsCommand

from oscar.apps.catalogue.notification import utils

Product = get_model('catalogue', 'product')
ProductNotification = get_model('notification', 'productnotification')

logger = logging.getLogger(__name__)


class Command(NoArgsCommand):
    """
    Check stock records of products for availability and send out notifications
    to customers that have subscribed to a notification email. Notifications
    for available products are disabled after an email has been send out.
    """
    help = _("Check check for notifications of products that are back in "
             "stock, send out emails and deactivate the notifications")

    def handle_noargs(self, **options):
        """
        Check all products with active product notifications for
        availability and send out email notifications when a product is
        available to buy.
        """
        logger.info('start searching for updated stock records')

        products = Product.objects.filter(
            productnotification__status=ProductNotification.ACTIVE
        )

        for product in products:
            logger.info('checking product availability for %s', product)
            if product.is_available_to_buy:
                logger.info('sending notifications for product %s', product)
                utils.send_email_notifications_for_product(product)
