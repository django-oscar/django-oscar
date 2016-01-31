import logging

from django.db import IntegrityError
from django.db.models import F
from django.dispatch import receiver

from oscar.apps.search.signals import user_search
from oscar.core.loading import get_class, get_classes

UserSearch, UserRecord, ProductRecord, UserProductView = get_classes(
    'analytics.models', ['UserSearch', 'UserRecord', 'ProductRecord',
                         'UserProductView'])
product_viewed = get_classes('catalogue.signals', ['product_viewed'])
basket_addition = get_class('basket.signals', 'basket_addition')
order_placed = get_class('order.signals', 'order_placed')

# Helpers

logger = logging.getLogger('oscar.analytics')


def _update_counter(model, field_name, filter_kwargs, increment=1):
    """
    Efficiently updates a counter field by a given increment. Uses Django's
    update() call to fetch and update in one query.

    :param model: The model class of the recording model
    :param field_name: The name of the field to update
    :param filter_kwargs: Parameters to the ORM's filter() function to get the
                          correct instance
    """
    try:
        record = model.objects.filter(**filter_kwargs)
        affected = record.update(**{field_name: F(field_name) + increment})
        if not affected:
            filter_kwargs[field_name] = increment
            model.objects.create(**filter_kwargs)
    except IntegrityError:
        # get_or_create sometimes fails due to MySQL's weird transactions, fail
        # silently
        logger.error(
            "IntegrityError when updating analytics counter for %s", model)


def _record_products_in_order(order):
    # surely there's a way to do this without causing a query for each line?
    for line in order.lines.all():
        _update_counter(
            ProductRecord, 'num_purchases',
            {'product': line.product}, line.quantity)


def _record_user_order(user, order):
    try:
        record = UserRecord.objects.filter(user=user)
        affected = record.update(
            num_orders=F('num_orders') + 1,
            num_order_lines=F('num_order_lines') + order.num_lines,
            num_order_items=F('num_order_items') + order.num_items,
            total_spent=F('total_spent') + order.total_incl_tax,
            date_last_order=order.date_placed)
        if not affected:
            UserRecord.objects.create(
                user=user, num_orders=1, num_order_lines=order.num_lines,
                num_order_items=order.num_items,
                total_spent=order.total_incl_tax,
                date_last_order=order.date_placed)
    except IntegrityError:
        logger.error(
            "IntegrityError in analytics when recording a user order.")


# Receivers

@receiver(product_viewed)
def receive_product_view(sender, product, user, **kwargs):
    if kwargs.get('raw', False):
        return
    _update_counter(ProductRecord, 'num_views', {'product': product})
    if user and user.is_authenticated():
        _update_counter(UserRecord, 'num_product_views', {'user': user})
        UserProductView.objects.create(product=product, user=user)


@receiver(user_search)
def receive_product_search(sender, query, user, **kwargs):
    if user and user.is_authenticated() and not kwargs.get('raw', False):
        UserSearch._default_manager.create(user=user, query=query)


@receiver(basket_addition)
def receive_basket_addition(sender, product, user, **kwargs):
    if kwargs.get('raw', False):
        return
    _update_counter(
        ProductRecord, 'num_basket_additions', {'product': product})
    if user and user.is_authenticated():
        _update_counter(UserRecord, 'num_basket_additions', {'user': user})


@receiver(order_placed)
def receive_order_placed(sender, order, user, **kwargs):
    if kwargs.get('raw', False):
        return
    _record_products_in_order(order)
    if user and user.is_authenticated():
        _record_user_order(user, order)
