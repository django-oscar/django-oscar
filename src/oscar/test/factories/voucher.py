import datetime

import factory
from django.utils.timezone import now

from oscar.apps.voucher.utils import get_unused_code
from oscar.core.loading import get_model
from oscar.test.factories import ConditionalOfferFactory

ConditionalOffer = get_model("offer", "ConditionalOffer")
Voucher = get_model("voucher", "Voucher")

__all__ = ["VoucherFactory", "VoucherSetFactory"]


class VoucherFactory(factory.django.DjangoModelFactory):
    name = "My voucher"
    code = "MYVOUCHER"
    usage = Voucher.MULTI_USE

    start_datetime = now() - datetime.timedelta(days=1)
    end_datetime = now() + datetime.timedelta(days=10)

    class Meta:
        model = get_model("voucher", "Voucher")


class VoucherSetFactory(factory.django.DjangoModelFactory):
    name = factory.Sequence(lambda n: "Voucher Set %d" % n)
    count = 100
    code_length = 12
    description = "Dummy description"
    start_datetime = now() - datetime.timedelta(days=1)
    end_datetime = now() + datetime.timedelta(days=10)

    class Meta:
        model = get_model("voucher", "VoucherSet")

    # pylint: disable=unused-argument
    @factory.post_generation
    def vouchers(obj, create, extracted, **kwargs):
        if not create:
            return
        offer = ConditionalOfferFactory(offer_type=ConditionalOffer.VOUCHER)
        for i in range(0, obj.count):
            voucher = Voucher.objects.create(
                name="%s - %d" % (obj.name, i + 1),
                code=get_unused_code(length=obj.code_length),
                voucher_set=obj,
                usage=Voucher.MULTI_USE,
                start_datetime=obj.start_datetime,
                end_datetime=obj.end_datetime,
            )
            voucher.offers.add(offer)
