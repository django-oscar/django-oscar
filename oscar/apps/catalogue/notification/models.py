from oscar.apps.catalogue.notification import abstract_models


class ProductNotification(abstract_models.AbstractProductNotification):
    pass


from oscar.apps.catalogue.notification.receivers import *
