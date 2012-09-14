from django.db.models import get_model

Notification = get_model('notifications', 'Notification')


def notify(user, msg, category=None):
    """
    Send a simple notification to a user
    """
    Notification.objects.create(
        recipient=user,
        subject=msg,
        category=category)

def send_message(user, subject, body, category):
    Notification.objects.create(
        recipient=user,
        subject=subject,
        body=body,
        category=category)
