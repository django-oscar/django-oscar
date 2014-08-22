from oscar.core.loading import is_model_registered
from oscar.apps.address.abstract_models import (
    AbstractUserAddress, AbstractCountry)


if not is_model_registered('address', 'UserAddress'):
    class UserAddress(AbstractUserAddress):
        pass


if not is_model_registered('address', 'Country'):
    class Country(AbstractCountry):
        pass
