import django

from oscar.core.loading import is_model_registered
from oscar.apps.analytics.abstract_models import (
    AbstractProductRecord, AbstractUserRecord,
    AbstractUserProductView, AbstractUserSearch)

__all__ = []


if not is_model_registered('analytics', 'ProductRecord'):
    class ProductRecord(AbstractProductRecord):
        pass

    __all__.append('ProductRecord')


if not is_model_registered('analytics', 'UserRecord'):
    class UserRecord(AbstractUserRecord):
        pass

    __all__.append('UserRecord')


if not is_model_registered('analytics', 'UserProductView'):
    class UserProductView(AbstractUserProductView):
        pass

    __all__.append('UserProductView')


if not is_model_registered('analytics', 'UserSearch'):
    class UserSearch(AbstractUserSearch):
        pass

    __all__.append('UserSearch')


if django.VERSION < (1, 7):
    from . import receivers  # noqa
