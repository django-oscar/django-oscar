import django.dispatch

product_viewed = django.dispatch.Signal(providing_args=["product", "user", "request", "response"])

# This needs to be moved into the search app when it is refactored
product_search = django.dispatch.Signal(providing_args=["query", '"user'])
