import django
from django.conf import settings

from oscar.apps.analytics.abstract_models import (
    AbstractProductRecord, AbstractUserRecord,
    AbstractUserProductView, AbstractUserSearch)


if 'analytics.ProductRecord' not in settings.OSCAR_OVERRIDE_MODELS:
    class ProductRecord(AbstractProductRecord):
        pass


if 'analytics.UserRecord' not in settings.OSCAR_OVERRIDE_MODELS:
    class UserRecord(AbstractUserRecord):
        pass


if 'analytics.UserProductView' not in settings.OSCAR_OVERRIDE_MODELS:
    class UserProductView(AbstractUserProductView):
        pass


if 'analytics.UserSearch' not in settings.OSCAR_OVERRIDE_MODELS:
    class UserSearch(AbstractUserSearch):
        pass


if django.VERSION < (1, 7):
    from .receivers import *  # noqa
