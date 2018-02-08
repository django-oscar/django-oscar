from oscar.core.loading import get_model

Notification = get_model('customer', 'Notification')


def notifications(request):
    ctx = {}
    if getattr(request, 'user', None) and request.user.is_authenticated:
        num_unread = Notification.objects.filter(
            recipient=request.user, date_read=None).count()
        ctx['num_unread_notifications'] = num_unread
    return ctx
