from django.db import models

from oscar.apps.catalogue.notification.abstract_models import AbstractNotification

Product = models.get_model('catalogue', 'Product')


class Notification(AbstractNotification):
    pass


class ProductNotification(Notification):
    """
    A product notification that is used to notify the set user when the
    specified product is back in stock.
    """
    item_field_name = "product"
    item_url_index = "catalogue:detail"
    product = models.ForeignKey(Product, db_index=True)


from oscar.apps.catalogue.notification.receivers import *
