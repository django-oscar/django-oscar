from django.utils.translation import gettext_lazy as _

from oscar.core.application import OscarConfig


class VoucherConfig(OscarConfig):
    label = "voucher"
    name = "oscar.apps.voucher"
    verbose_name = _("Voucher")

    def ready(self):
        # pylint: disable=unused-import
        from . import receivers
