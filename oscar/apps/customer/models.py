from oscar.apps.customer import abstract_models


class Email(abstract_models.AbstractEmail):
    pass


class CommunicationEventType(abstract_models.AbstractCommunicationEventType):
    pass


class Notification(abstract_models.AbstractNotification):
    pass


class ProductAlert(abstract_models.AbstractProductAlert):
    pass


from oscar.apps.customer.history_helpers import *
from oscar.apps.customer.alerts.receivers import *