from django.dispatch import receiver

from oscar.analytics.abstract_models import AbstractProductRecord, AbstractUserRecord
from oscar.services import import_module

product_signals = import_module('product.signals', ['product_viewed'])
basket_signals = import_module('basket.signals', ['basket_addition'])
order_signals = import_module('order.signals', ['order_placed'])

class ProductRecord(AbstractProductRecord):
    pass

class UserRecord(AbstractUserRecord):
    pass

# Helpers

def _record_product_view(product):
    record,_ = ProductRecord.objects.get_or_create(product=product)
    record.num_views += 1
    record.save()
    
def _record_user_product_view(user, product):
    if user.is_authenticated():
        record,_ = UserRecord.objects.get_or_create(user=user)
        record.num_product_views += 1
        record.save()
        
def _record_basket_addition(product):
    record,_ = ProductRecord.objects.get_or_create(product=product)
    record.num_basket_additions += 1
    record.save()
    
def _record_user_basket_addition(user, product):
    if user.is_authenticated():
        record,_ = UserRecord.objects.get_or_create(user=user)
        record.num_basket_additions += 1
        record.save()

def _record_products_in_order(order):
    for line in order.lines.all():
        record,_ = ProductRecord.objects.get_or_create(product=line.product)
        record.num_purchases += line.quantity
        record.save()

def _record_user_order(user, order):
    if user.is_authenticated():
        record,_ = UserRecord.objects.get_or_create(user=user)
        record.num_orders += 1
        record.num_order_lines += order.num_lines
        record.num_order_items += order.num_items
        record.total_spent += order.total_incl_tax
        record.date_last_order = order.date_placed
        record.save()

# Receivers

@receiver(product_signals.product_viewed)
def receive_product_view(sender, product, user, **kwargs):
    _record_product_view(product)
    _record_user_product_view(user, product)
    
@receiver(basket_signals.basket_addition)
def receive_basket_addition(sender, product, user, **kwargs):
    _record_basket_addition(product)
    _record_user_basket_addition(user, product)
    
@receiver(order_signals.order_placed)
def receive_order_placed(sender, order, user, **kwargs):
    _record_products_in_order(order)
    _record_user_order(user, order)