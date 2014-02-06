import factory
from oscar.apps.address import models
from oscar.core.compat import get_user_model

class UserFactory(factory.DjangoModelFactory):
    FACTORY_FOR = get_user_model()

    first_name = 'Oscar'
    last_name = 'Ecommerce'
    username = 'oscar'
    password = 'oscar'
    is_active = True
    is_superuser = False

class CountryFactory(factory.DjangoModelFactory):
    FACTORY_FOR = models.Country

    iso_3166_1_a2='GB' 
    name="UNITED KINGDOM"

class UserAddressFactory(factory.DjangoModelFactory):
    FACTORY_FOR = models.UserAddress

    title="Dr"
    first_name="Barry"
    last_name='Barrington'
    line1="1 King Road"
    line4="London"
    postcode="SW1 9RE"
    country = factory.SubFactory(CountryFactory)
    user = factory.SubFactory(UserFactory)
