import django.dispatch

basket_addition = django.dispatch.Signal(
    providing_args=["product", "user", "request", "quantity", "purchase_info"])
basket_removal = django.dispatch.Signal(
    providing_args=["product", "user", "request", "quantity", "purchase_info"])
voucher_addition = django.dispatch.Signal(
    providing_args=["basket", "voucher"])
voucher_removal = django.dispatch.Signal(
    providing_args=["basket", "voucher"])


def send_basket_variations_signals(
        lines_before, lines_after, user, request=None, sender=None):
    """

    Send all basket lines variations signals

    Args:
        lines_before (dict): A dict with lines (keys) and quantities (values)
            before basket variation(s)
        lines_after (dict): A dict with lines (keys) and quantities (values)
            after basket variation(s)
        user: The basket owner
        request: The request instance or None
        sender: The sender of the signal either a specific object or None

    """
    variations = {}
    for line, quantity in lines_before.items():
        variations[line] = variations.get(line, 0) - quantity
    for line, quantity in lines_after.items():
        variations[line] = variations.get(line, 0) + quantity

    # ``variations`` is a dict with lines as keys and quantity
    # variations as values
    for line, quantity_variance in variations.items():
        signal_kwargs = {
            'sender': sender,
            'product': line.product,
            'request': request,
            'user': user,
            'quantity': abs(variations[line]),
            'purchase_info': line.purchase_info}
        if quantity_variance > 0:
            basket_addition.send(**signal_kwargs)
        elif quantity_variance < 0:
            basket_removal.send(**signal_kwargs)
        else:
            pass
