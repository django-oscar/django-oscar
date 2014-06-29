import django

from oscar.apps.analytics.abstract_models import (
    AbstractProductRecord, AbstractUserRecord,
    AbstractUserProductView, AbstractUserSearch)


class ProductRecord(AbstractProductRecord):
    pass


class UserRecord(AbstractUserRecord):
    pass


class UserProductView(AbstractUserProductView):
    pass


class UserSearch(AbstractUserSearch):
    pass


if django.VERSION < (1, 7):
    from . import receivers  # noqa
