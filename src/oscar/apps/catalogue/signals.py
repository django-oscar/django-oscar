import django.dispatch

product_viewed = django.dispatch.Signal(
    providing_args=["product", "user", "request", "response"])
