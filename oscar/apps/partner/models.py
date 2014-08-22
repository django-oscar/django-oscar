import django

from oscar.core.loading import is_model_registered
from oscar.apps.address.abstract_models import AbstractPartnerAddress
from oscar.apps.partner.abstract_models import (
    AbstractPartner, AbstractStockRecord, AbstractStockAlert)


if not is_model_registered('partner', 'Partner'):
    class Partner(AbstractPartner):
        pass


if not is_model_registered('partner', 'PartnerAddress'):
    class PartnerAddress(AbstractPartnerAddress):
        pass


if not is_model_registered('partner', 'StockRecord'):
    class StockRecord(AbstractStockRecord):
        pass


if not is_model_registered('partner', 'StockAlert'):
    class StockAlert(AbstractStockAlert):
        pass


if django.VERSION < (1, 7):
    from . import receivers  # noqa
