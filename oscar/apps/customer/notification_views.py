import datetime

from django.views import generic
from django.db.models import get_model


class InboxView(generic.ListView):
    model = get_model('notifications', 'Notification')
    template_name = 'notifications/list.html'
    context_object_name = 'notifications'

    def get_queryset(self):
        # By default show only inbox messages
        qs = self.model._default_manager.filter(
            recipient=self.request.user,
            location=self.model.INBOX)
        self.mark_as_read(qs)
        return qs

    def mark_as_read(self, queryset):
        now = datetime.datetime.now()
        queryset.update(date_read=now)


class ArchiveView(generic.ListView):
    model = get_model('notifications', 'Notification')
    template_name = 'notifications/list.html'
    context_object_name = 'notifications'

    def get_queryset(self):
        qs = self.model._default_manager.filter(
            recipient=self.request.user,
            location=self.model.ARCHIVE)
        return qs
