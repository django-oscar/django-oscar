import django.dispatch

basket_addition = django.dispatch.Signal(
    providing_args=["product", "user", "request"])
