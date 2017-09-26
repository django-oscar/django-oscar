from oscar.core.loading import get_model

Notification = get_model('customer', 'Notification')


def notify_user(user, subject, **kwargs):
    """
    Send a simple notification to a user
    """
    Notification.objects.create(recipient=user, subject=subject, **kwargs)


def notify_users(users, subject, **kwargs):
    """
    Send a simple notification to an iterable of users
    """
    for user in users:
        notify_user(user, subject, **kwargs)
