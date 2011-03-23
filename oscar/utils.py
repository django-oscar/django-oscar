from oscar.product.models import ItemClass, Item
from oscar.stock.models import Partner, StockRecord

def create_product(price=None):
    u"""
    Helper method for creating products that are used in 
    tests.
    """
    ic,_ = ItemClass.objects.get_or_create(name="Dummy item class")
    item = Item.objects.create(title="Dummy product", item_class=ic)
    if price:
        partner,_ = Partner.objects.get_or_create(name="Dummy partner")
        sr = StockRecord.objects.create(product=item, partner=partner, price_excl_tax=price)
    return item