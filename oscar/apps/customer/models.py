from django.conf import settings

from oscar.apps.customer import abstract_models

if 'customer.Email' not in settings.OSCAR_OVERRIDE_MODELS:
    class Email(abstract_models.AbstractEmail):
        pass


if 'customer.CommunicationEventType' not in settings.OSCAR_OVERRIDE_MODELS:
    class CommunicationEventType(abstract_models.AbstractCommunicationEventType):
        pass


if 'customer.Notification' not in settings.OSCAR_OVERRIDE_MODELS:
    class Notification(abstract_models.AbstractNotification):
        pass


if 'customer.ProductAlert' not in settings.OSCAR_OVERRIDE_MODELS:
    class ProductAlert(abstract_models.AbstractProductAlert):
        pass


from oscar.apps.customer.history import *  # noqa
from oscar.apps.customer.alerts.receivers import *  # noqa
