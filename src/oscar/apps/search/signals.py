from __future__ import unicode_literals

from django.dispatch import Signal

user_search = Signal(providing_args=["session_id", "user", "query"])
