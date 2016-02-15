import factory

from oscar.core.loading import get_model
from oscar.core.phonenumber import PhoneNumber

__all__ = [
    'CountryFactory', 'UserAddressFactory',
]


class CountryFactory(factory.DjangoModelFactory):
    iso_3166_1_a2 = 'GB'
    printable_name = "UNITED KINGDOM"

    class Meta:
        model = get_model('address', 'Country')
        django_get_or_create = ('iso_3166_1_a2',)


class UserAddressFactory(factory.DjangoModelFactory):
    title = "Dr"
    first_name = "Barry"
    last_name = 'Barrington'
    line1 = "1 King Road"
    line4 = "London"
    postcode = "SW1 9RE"
    phone_number = PhoneNumber.from_string('+49 351 3296645')
    country = factory.SubFactory(CountryFactory)
    user = factory.SubFactory(
        'oscar.test.factories.UserFactory')

    class Meta:
        model = get_model('address', 'UserAddress')
