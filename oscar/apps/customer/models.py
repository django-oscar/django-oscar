import django

from oscar.core.loading import is_model_registered
from oscar.apps.customer import abstract_models


if not is_model_registered('customer', 'Email'):
    class Email(abstract_models.AbstractEmail):
        pass


if not is_model_registered('customer', 'CommunicationEventType'):
    class CommunicationEventType(
            abstract_models.AbstractCommunicationEventType):
        pass


if not is_model_registered('customer', 'Notification'):
    class Notification(abstract_models.AbstractNotification):
        pass


if not is_model_registered('customer', 'ProductAlert'):
    class ProductAlert(abstract_models.AbstractProductAlert):
        pass


if django.VERSION < (1, 7):
    from .receivers import *  # noqa
    from .alerts import receivers  # noqa
