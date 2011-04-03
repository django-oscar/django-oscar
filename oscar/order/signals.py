import django.dispatch

order_placed = django.dispatch.Signal(providing_args=["order", "user"])