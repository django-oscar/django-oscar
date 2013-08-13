from decimal import Decimal as D

from oscar.test import factories


def add_product(basket, price=None, quantity=1, product=None):
    """
    Helper to add a product to the basket.
    """
    if price is None:
        price = D('1')
    record = factories.create_stockrecord(
        product=product, price_excl_tax=price)
    info = factories.create_stockinfo(record)
    basket.add_product(record.product, info, quantity)


def add_products(basket, args):
    """
    Helper to add a series of products to the passed basket
    """
    for price, quantity in args:
        add_product(basket, price, quantity)
