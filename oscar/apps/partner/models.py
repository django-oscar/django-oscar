import django
from django.conf import settings

from oscar.apps.address.abstract_models import AbstractPartnerAddress
from oscar.apps.partner.abstract_models import (
    AbstractPartner, AbstractStockRecord, AbstractStockAlert)


if 'partner.Partner' not in settings.OSCAR_OVERRIDE_MODELS:
    class Partner(AbstractPartner):
        pass


if 'partner.PartnerAddress' not in settings.OSCAR_OVERRIDE_MODELS:
    class PartnerAddress(AbstractPartnerAddress):
        pass


if 'partner.StockRecord' not in settings.OSCAR_OVERRIDE_MODELS:
    class StockRecord(AbstractStockRecord):
        pass


if 'partner.StockAlert' not in settings.OSCAR_OVERRIDE_MODELS:
    class StockAlert(AbstractStockAlert):
        pass


if django.VERSION < (1, 7):
    from oscar.apps.partner import receivers

    receivers.register()
