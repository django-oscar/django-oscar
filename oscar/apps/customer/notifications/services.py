from oscar.core.loading import get_model

Notification = get_model('customer', 'Notification')


def notify_user(user, msg, category=None):
    """
    Send a simple notification to a user
    """
    Notification.objects.create(
        recipient=user,
        subject=msg,
        category=category)


def notify_users(users, msg, category=None):
    """
    Send a simple notification to an iterable of users
    """
    for user in users:
        notify_user(user, msg, category)
