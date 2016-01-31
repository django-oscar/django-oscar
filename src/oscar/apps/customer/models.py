from oscar.apps.customer import abstract_models
from oscar.core.loading import is_model_registered

__all__ = []


if not is_model_registered('customer', 'Email'):
    class Email(abstract_models.AbstractEmail):
        pass

    __all__.append('Email')


if not is_model_registered('customer', 'CommunicationEventType'):
    class CommunicationEventType(
            abstract_models.AbstractCommunicationEventType):
        pass

    __all__.append('CommunicationEventType')


if not is_model_registered('customer', 'Notification'):
    class Notification(abstract_models.AbstractNotification):
        pass

    __all__.append('Notification')


if not is_model_registered('customer', 'ProductAlert'):
    class ProductAlert(abstract_models.AbstractProductAlert):
        pass

    __all__.append('ProductAlert')
