from django.conf import settings

from oscar.apps.address.abstract_models import (
    AbstractUserAddress, AbstractCountry)


if 'address.UserAddress' not in settings.OSCAR_OVERRIDE_MODELS:
    class UserAddress(AbstractUserAddress):
        pass


if 'address.Country' not in settings.OSCAR_OVERRIDE_MODELS:
    class Country(AbstractCountry):
        pass
