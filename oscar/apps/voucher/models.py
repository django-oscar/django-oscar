import django

from oscar.apps.voucher.abstract_models import (
    AbstractVoucher, AbstractVoucherApplication)


class Voucher(AbstractVoucher):
    pass


class VoucherApplication(AbstractVoucherApplication):
    pass


if django.VERSION < (1, 7):
    from . import receivers  # noqa
