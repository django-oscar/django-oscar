from oscar.apps.customer.abstract_models import (
    AbstractEmail, AbstractCommunicationEventType, AbstractNotification)


class Email(AbstractEmail):
    pass


class CommunicationEventType(AbstractCommunicationEventType):
    pass


class Notification(AbstractNotification):
    pass


from oscar.apps.customer.history_helpers import *