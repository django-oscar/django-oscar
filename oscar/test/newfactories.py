"""
Factories using factory boy.

Using a silly module name as I don't want to mix the old and new
implementations of factories, but I do want to allow importing both from the
same place.
"""
import factory

from oscar.apps.address import models as address_models
from oscar.core.compat import get_user_model

__all__ = ["UserFactory", "CountryFactory", "UserAddressFactory"]


class UserFactory(factory.DjangoModelFactory):
    FACTORY_FOR = get_user_model()

    email = 'the_j_meister@example.com'
    first_name = 'joseph'
    last_name = 'winterbottom'
    username = 'the_j_meister'
    password = factory.PostGenerationMethodCall('set_password', 'skelebrain')
    is_active = True
    is_superuser = False
    is_staff = False


class CountryFactory(factory.DjangoModelFactory):
    FACTORY_FOR = address_models.Country

    iso_3166_1_a2 = 'GB'
    name = "UNITED KINGDOM"


class UserAddressFactory(factory.DjangoModelFactory):
    FACTORY_FOR = address_models.UserAddress

    title = "Dr"
    first_name = "Barry"
    last_name = 'Barrington'
    line1 = "1 King Road"
    line4 = "London"
    postcode = "SW1 9RE"
    country = factory.SubFactory(CountryFactory)
    user = factory.SubFactory(UserFactory)
