from decimal import Decimal as D

from oscar.apps.offer import models


class ChangesOwnerName(models.Benefit):

    class Meta:
        proxy = True

    def apply(self, basket, condition, offer=None):
        basket.owner.first_name = "Terry"
        basket.owner.save()
        return D('0.00')

    @property
    def description(self):
        return "Changes owners name"
