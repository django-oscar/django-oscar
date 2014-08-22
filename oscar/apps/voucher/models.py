import django

from oscar.core.loading import is_model_registered
from oscar.apps.voucher.abstract_models import (
    AbstractVoucher, AbstractVoucherApplication)


if not is_model_registered('voucher', 'Voucher'):
    class Voucher(AbstractVoucher):
        pass


if not is_model_registered('voucher', 'VoucherApplication'):
    class VoucherApplication(AbstractVoucherApplication):
        pass


if django.VERSION < (1, 7):
    from . import receivers  # noqa
