import django.dispatch

review_added = django.dispatch.Signal(
    providing_args=["review", "user", "request", "response"])
