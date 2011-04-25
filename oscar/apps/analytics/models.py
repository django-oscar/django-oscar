from oscar.apps.analytics.abstract_models import (AbstractProductRecord, AbstractUserRecord,
                                                  AbstractUserProductView, AbstractUserSearch)


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