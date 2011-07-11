import django.dispatch

product_viewed = django.dispatch.Signal(providing_args=["product", "user", "request", "response"])
product_search = django.dispatch.Signal(providing_args=["query", '"user'])
