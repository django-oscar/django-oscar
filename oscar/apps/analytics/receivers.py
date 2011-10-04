from django.dispatch import receiver
from django.db import IntegrityError
import logging

from oscar.core.loading import import_module
import_module('analytics.models', ['UserRecord', 'ProductRecord', 'UserProductView'], locals())
import_module('catalogue.signals', ['product_viewed', 'product_search'], locals())
import_module('basket.signals', ['basket_addition'], locals())
import_module('order.signals', ['order_placed'], locals())

# Helpers

logger = logging.getLogger('oscar.analytics')

def _record_product_view(product):
    try:
        record,_ = ProductRecord.objects.get_or_create(product=product)
        record.num_views += 1
        record.save()
    except IntegrityError:
        # get_or_create sometimes fails due to MySQL's weird transactions, fail silently
        logger.error("IntegrityError on ProductRecord.objects.get_or_create(product=product)")
    
def _record_user_product_view(user, product):
    if user.is_authenticated():
        # Update user record
        try:
            record,_ = UserRecord.objects.get_or_create(user=user)
            record.num_product_views += 1
            record.save()
        except IntegrityError:
            logger.error("IntegrityError on UserRecord.objects.get_or_create(user=user)")
        
        # Add user product view record
        UserProductView.objects.create(product=product, user=user)

def _record_basket_addition(product):
    try:
        record,_ = ProductRecord.objects.get_or_create(product=product)
        record.num_basket_additions += 1
        record.save()
    except IntegrityError:
        logger.error("IntegrityError on ProductRecord.objects.get_or_create(product=product)")
    
def _record_user_basket_addition(user, product):
    if user.is_authenticated():
        try:
            record,_ = UserRecord.objects.get_or_create(user=user)
            record.num_basket_additions += 1
            record.save()
        except IntegrityError:
            logger.error("IntegrityError on UserRecord.objects.get_or_create(user=user)")

def _record_products_in_order(order):
    for line in order.lines.all():
        try:
            record,_ = ProductRecord.objects.get_or_create(product=line.product)
            record.num_purchases += line.quantity
            record.save()
        except IntegrityError:
            logger.error("IntegrityError on ProductRecord.objects.get_or_create(product=product)")

def _record_user_order(user, order):
    if user.is_authenticated():
        try:
            record,_ = UserRecord.objects.get_or_create(user=user)
            record.num_orders += 1
            record.num_order_lines += order.num_lines
            record.num_order_items += order.num_items
            record.total_spent += order.total_incl_tax
            record.date_last_order = order.date_placed
            record.save()
        except IntegrityError:
            logger.error("IntegrityError on UserRecord.objects.get_or_create(user=user)")

def _record_user_product_search(user, query):
    if user.is_authenticated():
        UserSearch._default_manager.create(user=user, query=query)

# Receivers

@receiver(product_viewed)
def receive_product_view(sender, product, user, **kwargs):
    _record_product_view(product)
    _record_user_product_view(user, product)
    
@receiver(product_search)
def receive_product_search(sender, query, user, **kwargs):
    _record_user_product_search(user, query)
    
@receiver(basket_addition)
def receive_basket_addition(sender, product, user, **kwargs):
    _record_basket_addition(product)
    _record_user_basket_addition(user, product)
    
@receiver(order_placed)
def receive_order_placed(sender, order, user, **kwargs):
    _record_products_in_order(order)
    _record_user_order(user, order)
