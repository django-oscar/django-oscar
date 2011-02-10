from django.db import models

from oscar.address.abstract_models import AbstractUserAddress, AbstractCountry


class UserAddress(AbstractUserAddress):
    pass


class Country(AbstractCountry):
    pass