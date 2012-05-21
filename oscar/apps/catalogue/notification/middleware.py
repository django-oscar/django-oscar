#from django.conf import settings
#from landmark.catalogue.notification.models import Notification
#
#class NotificationMiddleware(object):
#    """
#
#    """
#    def process_request(self, request):
#        if request.user.is_authenticated():
#            # nothing to do here
#            return None
#
#        key = request.COOKIES.get(settings.NOTIFICATION_COOKIE_NAME, None)
#        if not key:
#            return None
#
#        # BAD!! We shuold have a key to pick the correct notification
#        try:
#            notification = Notification.objects.get(email=key)
#        except Notification.DoesNotExist:
#            return None
#
#        setattr(request.user, 'notification', notification)
#
#
