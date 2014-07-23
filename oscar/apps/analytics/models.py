import django

from oscar.core.loading import is_model_registered
from oscar.apps.analytics.abstract_models import (
    AbstractProductRecord, AbstractUserRecord,
    AbstractUserProductView, AbstractUserSearch)


if not is_model_registered('analytics', 'ProductRecord'):
    class ProductRecord(AbstractProductRecord):
        pass


if not is_model_registered('analytics', 'UserRecord'):
    class UserRecord(AbstractUserRecord):
        pass


if not is_model_registered('analytics', 'UserProductView'):
    class UserProductView(AbstractUserProductView):
        pass


if not is_model_registered('analytics', 'UserSearch'):
    class UserSearch(AbstractUserSearch):
        pass


if django.VERSION < (1, 7):
    from . import receivers  # noqa
