from decimal import Decimal as D

import factory

from oscar.core.loading import get_model

__all__ = [
    'LegalEntityAddressFactory', 'LegalEntityFactory',
    'PartnerFactory', 'StockRecordFactory',
]


class PartnerFactory(factory.DjangoModelFactory):
    name = "Gardners"

    class Meta:
        model = get_model('partner', 'Partner')

    @factory.post_generation
    def users(self, create, extracted, **kwargs):
        if not create:
            return

        if extracted:
            for user in extracted:
                self.users.add(user)


class StockRecordFactory(factory.DjangoModelFactory):
    partner = factory.SubFactory(PartnerFactory)
    partner_sku = factory.Sequence(lambda n: 'unit%d' % n)
    price_currency = "GBP"
    price_excl_tax = D('9.99')
    num_in_stock = 100

    class Meta:
        model = get_model('partner', 'StockRecord')


class LegalEntityFactory(factory.DjangoModelFactory):
    business_name = 'Test Company'
    vat_number = 'test-vat-number'

    class Meta:
        model = get_model('partner', 'LegalEntity')


class LegalEntityAddressFactory(factory.DjangoModelFactory):
    legal_entity = factory.SubFactory(LegalEntityFactory)
    line1 = '1 Egg Street'
    line2 = 'London'
    postcode = 'N12 9RE'
    country = factory.SubFactory('oscar.test.factories.CountryFactory')

    class Meta:
        model = get_model('partner', 'LegalEntityAddress')
