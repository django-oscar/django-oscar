import datetime

import factory
from django.utils.timezone import now

from oscar.core.loading import get_model
from oscar.test.factories import ConditionalOfferFactory


__all__ = ['VoucherFactory', 'VoucherSetFactory']


class VoucherFactory(factory.DjangoModelFactory):
    name = "My voucher"
    code = "MYVOUCHER"

    start_datetime = now() - datetime.timedelta(days=1)
    end_datetime = now() + datetime.timedelta(days=10)

    class Meta:
        model = get_model('voucher', 'Voucher')


class VoucherSetFactory(factory.DjangoModelFactory):
    name = factory.Sequence(lambda n: 'Voucher Set %d' % n)
    count = 100
    code_length = 12
    start_datetime = now() - datetime.timedelta(days=1)
    end_datetime = now() + datetime.timedelta(days=10)
    offer = factory.SubFactory(ConditionalOfferFactory)

    class Meta:
        model = get_model('voucher', 'VoucherSet')
