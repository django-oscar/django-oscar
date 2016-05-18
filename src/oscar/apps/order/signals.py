import django.dispatch

order_placed = django.dispatch.Signal(providing_args=["order", "user"])

order_status_changed = django.dispatch.Signal(
    providing_args=["order", "old_status", "new_status"])

order_line_status_changed = django.dispatch.Signal(
    providing_args=["line", "old_status", "new_status"])
