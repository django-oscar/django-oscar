# coding=utf-8
import factory
from oscar.apps.address import models
from oscar.core.compat import get_user_model

class UserFactory(factory.DjangoModelFactory):
    FACTORY_FOR = get_user_model()

    first_name = u'Oѕｃâｒ'
    last_name = u'Ecömmerce'
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
    first_name=u"Bärry"
    last_name=u'Bärrington'
    line1=u"1 King Roäd"
    line4=u"Löndön"
    postcode="SW1 9RE"
    country = factory.SubFactory(CountryFactory)
    user = factory.SubFactory(UserFactory)
