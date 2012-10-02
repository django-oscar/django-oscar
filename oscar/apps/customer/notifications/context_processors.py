from django.db.models import get_model

Notification = get_model('customer', 'Notification')


def notifications(request):
    ctx = {}
    if request.user.is_authenticated():
        num_unread = Notification.objects.filter(
            recipient=request.user, date_read=None).count()
        ctx['num_unread_notifications'] = num_unread
    return ctx
