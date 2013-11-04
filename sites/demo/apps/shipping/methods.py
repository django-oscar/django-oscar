from decimal import Decimal as D
from django.template.loader import render_to_string

from oscar.apps.shipping import base


class Standard(base.Base):
    code = 'standard'
    name = 'Standard shipping'
    is_tax_known = True

    charge_per_item = D('0.99')
    threshold = D('12.00')

    description = render_to_string(
        'shipping/standard.html', {
            'charge_per_item': charge_per_item,
            'threshold': threshold})

    @property
    def charge_incl_tax(self):
        # Free for orders over some threshold
        if self.basket.total_incl_tax > self.threshold:
            return D('0.00')

        # Simple method - charge 0.99 per item
        total = D('0.00')
        for line in self.basket.all_lines():
            total += line.quantity * self.charge_per_item
        return total

    @property
    def charge_excl_tax(self):
        # Assume no tax
        return self.basket_charge_incl_tax()


class Express(base.Base):
    code = 'express'
    name = 'Express shipping'
    is_tax_known = True

    charge_per_item = D('1.50')
    description = render_to_string(
        'shipping/express.html', {'charge_per_item': charge_per_item})

    @property
    def charge_incl_tax(self):
        # Simple method - charge 0.99 per item
        total = D('0.00')
        for line in self.basket.all_lines():
            total += line.quantity * self.charge_per_item
        return total

    @property
    def charge_excl_tax(self):
        # Assume no tax
        return self.basket_charge_incl_tax()
