from django.apps import AppConfig


class CustomerConfig(AppConfig):
    app_label = 'customer'
    name = 'oscar.apps.customer'

    def ready(self):
        from oscar.apps.customer.history import *  # noqa
        from oscar.apps.customer.alerts.receivers import *  # noqa

        return super(CustomerConfig, self).ready()
