from decimal import Decimal as D

from django.conf import settings
from django.utils.translation import gettext_lazy as _
from oscar.apps.shipping import methods


class FlatRate(methods.FixedPrice):
    """Same delivery charge for every order (KHAFA_SHIPPING_CHARGE, tax
    included), for the website and the mobile app"""

    code = "flat-rate"
    name = _("Standard delivery")

    def __init__(self):
        charge = D(settings.KHAFA_SHIPPING_CHARGE)
        super().__init__(charge_excl_tax=charge, charge_incl_tax=charge)
