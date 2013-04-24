from decimal import Decimal as D
from django.template.loader import render_to_string

from oscar.apps.shipping import base


class Standard(base.ShippingMethod):
    code = 'standard'
    name = 'Standard shipping'
    description = render_to_string('shipping/standard.html')

    def basket_charge_incl_tax(self):
        # Free for orders over some threshold
        if self.basket.total_incl_tax > D('12.00'):
            return D('0.00')

        # Simple method - charge 0.99 per item
        total = D('0.00')
        charge_per_item = D('0.99')
        for line in self.basket.all_lines():
            total += line.quantity * charge_per_item
        return total

    def basket_charge_excl_tax(self):
        # Assume no tax
        return self.basket_charge_incl_tax()


class Express(base.ShippingMethod):
    code = 'express'
    name = 'Express shipping'
    description = render_to_string('shipping/express.html')

    def basket_charge_incl_tax(self):
        # Simple method - charge 0.99 per item
        total = D('0.00')
        charge_per_item = D('1.50')
        for line in self.basket.all_lines():
            total += line.quantity * charge_per_item
        return total

    def basket_charge_excl_tax(self):
        # Assume no tax
        return self.basket_charge_incl_tax()
