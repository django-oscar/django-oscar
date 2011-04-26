from django.dispatch import Signal, receiver

pre_payment = Signal(providing_args=["view"])
post_payment = Signal(providing_args=["view"])
order_placed = Signal(providing_args=["order"])

@receiver(order_placed)
def update_stock_levels(sender, **kwargs):
    u"""Updated a line item's stock level"""
    order = kwargs['order']
    for line in order.lines.all():
        sr = line.product.stockrecord
        sr.decrement_num_in_stock(line.quantity)