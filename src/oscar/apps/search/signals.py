from django.dispatch import Signal

user_search = Signal(providing_args=["session_id", "user", "query"])
