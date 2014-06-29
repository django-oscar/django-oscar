from django.conf import settings

from oscar.apps.address.abstract_models import AbstractPartnerAddress
from oscar.apps.partner.abstract_models import (
    AbstractPartner, AbstractStockRecord, AbstractStockAlert)


if not 'partner.Partner' in settings.OSCAR_OVERRIDE_MODELS:
    class Partner(AbstractPartner):
        pass


if not 'partner.PartnerAddress' in settings.OSCAR_OVERRIDE_MODELS:
    class PartnerAddress(AbstractPartnerAddress):
        pass


if not 'partner.StockRecord' in settings.OSCAR_OVERRIDE_MODELS:
    class StockRecord(AbstractStockRecord):
        pass


if not 'partner.StockAlert' in settings.OSCAR_OVERRIDE_MODELS:
    class StockAlert(AbstractStockAlert):
        pass


from oscar.apps.partner.receivers import *  # noqa
