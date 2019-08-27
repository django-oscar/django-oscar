import warnings

from oscar.core.loading import get_class
from oscar.utils.deprecation import RemovedInOscar22Warning

Dispatcher = get_class('communication.utils', 'Dispatcher')


def notify_user(user, subject, **kwargs):
    warnings.warn(
        'Use of `notify_user` is deprecated. Please use `notify_user` '
        'method of `communications.utils.Dispatcher`.',
        RemovedInOscar22Warning,
        stacklevel=2,
    )
    Dispatcher().notify_user(user, subject, **kwargs)


def notify_users(users, subject, **kwargs):
    warnings.warn(
        'Use of `notify_users` is deprecated. Please use `notify_users` '
        'method of `communications.utils.Dispatcher`.',
        RemovedInOscar22Warning,
        stacklevel=2,
    )
    Dispatcher().notify_users(users, subject, **kwargs)
