from django.db import models
from django.utils.translation import ugettext as _

from model_utils.managers import InheritanceManager

from oscar.apps.catalogue.models import Product
from oscar.apps.catalogue.notification.abstract_models import AbstractNotification


class Notification(AbstractNotification):
    objects = InheritanceManager()

    def get_notification_item(self):
        """
        Get notification item which returns ``None`` as ``Notification``
        does only provide base class functionalities.
        """
        return None


class ProductNotification(Notification):
    """
    A product notification that is used to notify the set user when the
    specified product is back in stock.
    """
    product = models.ForeignKey(Product, db_index=True)

    @models.permalink
    def get_confirm_url(self):
        """
        Get confirmation URL for this specific notification/user combo.
        """
        return ('notification-confirm', (), {
            'slug': self.product.slug,
            'pk': self.product.id,
            'key': self.confirm_key
        })

    @models.permalink
    def get_unsubscribe_url(self):
        """
        Get unsubscribtion URL for this specific notification/user combo.
        """
        return ('notification-unsubscribe', (), {
            'slug': self.product.slug,
            'pk': self.product.id,
            'key': self.confirm_key
        })

    def get_notification_item(self):
        """
        Get notification item which is an instance of ``Product`` for
        ``ProductNotification``.
        """
        return self.product


from oscar.apps.catalogue.notification.receivers import *
