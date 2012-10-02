from django.core.urlresolvers import reverse
from django.utils.translation import ugettext_lazy as _, ungettext
from django.utils.timezone import now
from django.contrib import messages
from django import http
from django.views import generic
from django.db.models import get_model

from oscar.views.generic import BulkEditMixin

Notification = get_model('customer', 'Notification')


class NotificationListView(generic.ListView):
    model = Notification
    template_name = 'customer/notifications/list.html'
    context_object_name = 'notifications'
    paginate_by = 20

    def get_context_data(self, **kwargs):
        ctx = super(NotificationListView, self).get_context_data(**kwargs)
        ctx['title'] = self.title
        ctx['list_type'] = self.list_type
        return ctx


class InboxView(NotificationListView):
    title = _("Notifications inbox")
    list_type = 'inbox'

    def get_queryset(self):
        qs = self.model._default_manager.filter(
            recipient=self.request.user,
            location=self.model.INBOX)
        for obj in qs:
            if not obj.is_read:
                setattr(obj, 'is_new', True)
        self.mark_as_read(qs)
        return qs

    def mark_as_read(self, queryset):
        unread = queryset.filter(date_read=None)
        unread.update(date_read=now())


class ArchiveView(NotificationListView):
    title = _("Archived notifications")
    list_type = 'archive'

    def get_queryset(self):
        return self.model._default_manager.filter(
            recipient=self.request.user,
            location=self.model.ARCHIVE)


class DetailView(generic.DetailView):
    model = Notification
    template_name = 'customer/notifications/detail.html'
    context_object_name = 'notification'

    def get_queryset(self):
        return self.model._default_manager.filter(
            recipient=self.request.user)


class UpdateView(BulkEditMixin, generic.RedirectView):
    model = Notification
    actions = ('archive', 'delete')
    checkbox_object_name = 'notification'

    def get_object_dict(self, ids):
        return self.model.objects.filter(
            recipient=self.request.user).in_bulk(ids)

    def get_success_response(self):
        default = reverse('customer:notifications-inbox')
        return http.HttpResponseRedirect(
            self.request.META.get('HTTP_REFERER', default))

    def archive(self, request, notifications):
        for notification in notifications:
            notification.archive()
        msg = ungettext(
            '%(count)d notification archived',
            '%(count)d notifications archived', len(notifications)) % {
                'count': len(notifications)}
        messages.success(request, msg)
        return self.get_success_response()

    def delete(self, request, notifications):
        for notification in notifications:
            notification.delete()
        msg = ungettext(
            '%(count)d notification deleted',
            '%(count)d notifications deleted', len(notifications)) % {
                'count': len(notifications)}
        messages.success(request, msg)
        return self.get_success_response()
