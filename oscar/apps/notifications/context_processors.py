from django.db.models import get_model

Notification = get_model('notifications', 'Notification')


def notifications(request):
    num_unread = Notification.objects.filter(
        recipient=request.user, date_read=None).count()
    return {'num_unread_notifications': num_unread}
