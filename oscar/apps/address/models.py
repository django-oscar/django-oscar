from oscar.core.loading import model_registered
from oscar.apps.address.abstract_models import (
    AbstractUserAddress, AbstractCountry)


if not model_registered('address', 'UserAddress'):
    class UserAddress(AbstractUserAddress):
        pass


if not model_registered('address', 'Country'):
    class Country(AbstractCountry):
        pass
