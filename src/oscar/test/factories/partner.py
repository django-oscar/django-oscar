from decimal import Decimal as D

import factory

from oscar.core.loading import get_model

__all__ = [
    "PartnerFactory",
    "StockRecordFactory",
]


class PartnerFactory(factory.django.DjangoModelFactory):
    name = "Gardners"

    class Meta:
        model = get_model("partner", "Partner")

    @factory.post_generation
    def users(self, create, extracted, **kwargs):
        if not create:
            return

        if extracted:
            for user in extracted:
                self.users.add(user)  # pylint: disable=E1101


class StockRecordFactory(factory.django.DjangoModelFactory):
    partner = factory.SubFactory(PartnerFactory)
    partner_sku = factory.Sequence(lambda n: "unit%d" % n)
    price_currency = "GBP"
    price = D("9.99")
    num_in_stock = 100

    class Meta:
        model = get_model("partner", "StockRecord")
