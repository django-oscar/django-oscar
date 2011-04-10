import django.dispatch

product_viewed = django.dispatch.Signal(providing_args=["product", '"user'])
product_search = django.dispatch.Signal(providing_args=["query", '"user'])