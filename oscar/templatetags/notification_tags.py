from django import template
from django.db.models import get_model

ProductNotification = get_model('notification', 'productnotification')

register = template.Library()


@register.assignment_tag
def has_product_notification(user, product):
    """
    Check if the user has already signed up to receive a notification
    for this product. Anonymous users are ignored. If a registered
    user has signed up for a notification the tag returns ``True``.
    It returns ``False`` in all other cases.
    """
    if not user.is_authenticated():
        return False

    return ProductNotification.objects.filter(user=user,
                                              product=product).count() > 0
