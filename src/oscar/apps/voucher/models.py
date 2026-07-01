from oscar.apps.voucher.abstract_models import (
    AbstractVoucher,
    AbstractVoucherApplication,
    AbstractVoucherSet,
)
from oscar.core.loading import is_model_registered

__all__ = []

if not is_model_registered("voucher", "VoucherSet"):

    class VoucherSet(AbstractVoucherSet):
        pass

    __all__.append("VoucherSet")


if not is_model_registered("voucher", "Voucher"):

    class Voucher(AbstractVoucher):
        pass

    __all__.append("Voucher")


if not is_model_registered("voucher", "VoucherApplication"):

    class VoucherApplication(AbstractVoucherApplication):
        pass

    __all__.append("VoucherApplication")
