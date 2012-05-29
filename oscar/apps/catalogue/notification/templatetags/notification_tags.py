from django import template

register = template.Library()

@register.assignment_tag
def has_signed_up(user, product):
    """
    Check if the user has already signed up to receive a notification
    for this product. Anonymous users are ignored. If a registered
    user has signed up for a notification the tag returns ``True``. 
    It returns ``False`` in all other cases.
    """
    if not user.is_authenticated():
        return False

    if user.notifications.filter(product=product).count() > 0:
        return True
    return False
