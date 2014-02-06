import factory
from oscar.apps.address import models

class UserAddressFactory(factory.DjangoModelFactory):
    FACTORY_FOR = models.UserAddress

    title="Dr"
    first_name="Barry"
    last_name='Barrington'
    line1="1 King Road"
    line4="London"
    postcode="SW1 9RE"
