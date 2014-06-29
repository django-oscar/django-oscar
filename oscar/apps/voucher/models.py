from django.conf import settings

from oscar.apps.voucher.abstract_models import (
    AbstractVoucher, AbstractVoucherApplication)


if 'voucher.Voucher' not in settings.OSCAR_OVERRIDE_MODELS:
    class Voucher(AbstractVoucher):
        pass


if 'voucher.VoucherApplication' not in settings.OSCAR_OVERRIDE_MODELS:
    class VoucherApplication(AbstractVoucherApplication):
        pass
