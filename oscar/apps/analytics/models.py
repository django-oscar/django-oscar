from oscar.apps.analytics.abstract_models import (AbstractProductRecord, AbstractUserRecord,
                                                  AbstractUserProductView, AbstractUserSearch)
from oscar.core.loading import import_module
product_signals = import_module('product.signals', ['product_viewed', 'product_search'])
basket_signals = import_module('basket.signals', ['basket_addition'])
order_signals = import_module('order.signals', ['order_placed'])


class ProductRecord(AbstractProductRecord):
    pass

class UserRecord(AbstractUserRecord):
    pass

class UserProductView(AbstractUserProductView):
    pass

class UserSearch(AbstractUserSearch):
    pass

# Import receiver functions
from oscar.apps.analytics.receivers import *