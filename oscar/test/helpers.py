from oscar.apps.product.models import ItemClass, Item
from oscar.apps.stock.models import Partner, StockRecord

def create_product(price=None, upc="dummy_upc"):
    u"""
    Helper method for creating products that are used in 
    tests.
    """
    ic,_ = ItemClass._default_manager.get_or_create(name="Dummy item class")
    item = Item._default_manager.create(title="Dummy product", item_class=ic, upc=upc)
    if price:
        partner,_ = Partner._default_manager.get_or_create(name="Dummy partner")
        sr = StockRecord._default_manager.create(product=item, partner=partner, price_excl_tax=price)
    return item