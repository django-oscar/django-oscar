import django

from oscar.apps.customer import abstract_models


class Email(abstract_models.AbstractEmail):
    pass


class CommunicationEventType(abstract_models.AbstractCommunicationEventType):
    pass


class Notification(abstract_models.AbstractNotification):
    pass


class ProductAlert(abstract_models.AbstractProductAlert):
    pass


if django.VERSION < (1, 7):
    from oscar.apps.customer.history import *  # noqa
    from .alerts import receivers  # noqa
