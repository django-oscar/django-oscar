from oscar.core.loading import is_model_registered
from oscar.apps.voucher.abstract_models import (
    AbstractVoucher, AbstractVoucherApplication)

__all__ = []


if not is_model_registered('voucher', 'Voucher'):
    class Voucher(AbstractVoucher):
        pass

    __all__.append('Voucher')


if not is_model_registered('voucher', 'VoucherApplication'):
    class VoucherApplication(AbstractVoucherApplication):
        pass

    __all__.append('VoucherApplication')
