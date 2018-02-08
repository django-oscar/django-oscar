from oscar.core.loading import is_model_registered

from .abstract_models import *  # noqa

__all__ = []


if not is_model_registered('communication', 'Email'):
    class Email(AbstractEmail):
        pass

    __all__.append('Email')


if not is_model_registered('communication', 'CommunicationEventType'):
    class CommunicationEventType(AbstractCommunicationEventType):
        pass

    __all__.append('CommunicationEventType')


if not is_model_registered('communication', 'Notification'):
    class Notification(AbstractNotification):
        pass

    __all__.append('Notification')
