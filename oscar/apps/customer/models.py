from oscar.apps.customer.abstract_models import AbstractEmail, AbstractCommunicationEventType


class Email(AbstractEmail):
    pass


class CommunicationEventType(AbstractCommunicationEventType):
    pass


from oscar.apps.customer.history_helpers import *