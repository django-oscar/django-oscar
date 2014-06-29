from django.apps import AppConfig


class CustomerConfig(AppConfig):
    label = 'customer'
    name = 'oscar.apps.customer'

    def ready(self):
        from oscar.apps.customer.history import *  # noqa
        from .alerts import receivers  # noqa
