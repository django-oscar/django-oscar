from oscar.apps.address.abstract_models import AbstractPartnerAddress
from oscar.apps.partner.abstract_models import (
    AbstractPartner, AbstractStockRecord, AbstractStockAlert)


class Partner(AbstractPartner):
    pass


class PartnerAddress(AbstractPartnerAddress):
    pass


class StockRecord(AbstractStockRecord):
    pass


class StockAlert(AbstractStockAlert):
    pass


from oscar.apps.partner.receivers import *  # noqa
