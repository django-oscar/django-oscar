from decimal import Decimal as D

from oscar.apps.offer.utils import Line
from oscar.test import factories


def add_line(set_of_lines, price=None, quantity=1, product=None):
    """
    Helper to add a product to the basket.
    """
    if price is None:
        price = D('1')
    if product and product.has_stockrecords:
        record = product.stockrecords.all()[0]
    else:
        record = factories.create_stockrecord(
            product=product, price_excl_tax=price,
            num_in_stock=quantity + 1)
        product = record.product

    set_of_lines.add_line(Line(None, product, record, quantity, price))
