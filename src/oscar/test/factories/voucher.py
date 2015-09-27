import datetime

import factory
from django.utils.timezone import now

from oscar.core.loading import get_model

__all__ = ['VoucherFactory']


class VoucherFactory(factory.DjangoModelFactory):
    name = "My voucher"
    code = "MYVOUCHER"

    start_datetime = now() - datetime.timedelta(days=1)
    end_datetime = now() + datetime.timedelta(days=10)

    class Meta:
        model = get_model('voucher', 'Voucher')
