from django.dispatch import Signal

user_registered = Signal(providing_args=["request", "user"])
user_logged_in = Signal(providing_args=["request", "user"])
