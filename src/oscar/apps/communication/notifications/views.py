from django.conf import settings
from django.contrib import messages
from django.utils.html import strip_tags
from django.utils.timezone import now
from django.utils.translation import gettext_lazy as _
from django.utils.translation import ngettext
from django.views import generic

from oscar.core.loading import get_class, get_model
from oscar.core.utils import redirect_to_referrer
from oscar.views.generic import BulkEditMixin

PageTitleMixin = get_class('customer.mixins', 'PageTitleMixin')
Notification = get_model('communication', 'Notification')


class NotificationListView(PageTitleMixin, generic.ListView):
    model = Notification
    template_name = 'oscar/communication/notifications/list.html'
    context_object_name = 'notifications'
    paginate_by = settings.OSCAR_NOTIFICATIONS_PER_PAGE
    page_title = _("Notifications")
    active_tab = 'notifications'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['list_type'] = self.list_type
        return ctx


class InboxView(NotificationListView):
    list_type = 'inbox'

    def get_queryset(self):
        return self.model._default_manager.filter(
            recipient=self.request.user,
            location=self.model.INBOX)


class ArchiveView(NotificationListView):
    list_type = 'archive'

    def get_queryset(self):
        return self.model._default_manager.filter(
            recipient=self.request.user,
            location=self.model.ARCHIVE)


class DetailView(PageTitleMixin, generic.DetailView):
    model = Notification
    template_name = 'oscar/communication/notifications/detail.html'
    context_object_name = 'notification'
    active_tab = 'notifications'

    def get_object(self, queryset=None):
        obj = super().get_object()
        if not obj.date_read:
            obj.date_read = now()
            obj.save()
        return obj

    def get_page_title(self):
        """Append subject to page title"""
        title = strip_tags(self.object.subject)
        return '%s: %s' % (_('Notification'), title)

    def get_queryset(self):
        return self.model._default_manager.filter(
            recipient=self.request.user)


class UpdateView(BulkEditMixin, generic.View):
    model = Notification
    http_method_names = ['post']
    actions = ('archive', 'delete')
    checkbox_object_name = 'notification'

    def get_object_dict(self, ids):
        return self.model.objects.filter(
            recipient=self.request.user).in_bulk(ids)

    def get_success_response(self):
        return redirect_to_referrer(
            self.request, 'communication:notifications-inbox')

    def archive(self, request, notifications):
        for notification in notifications:
            notification.archive()
        msg = ngettext(
            '%(count)d notification archived',
            '%(count)d notifications archived', len(notifications)) \
            % {'count': len(notifications)}
        messages.success(request, msg)
        return self.get_success_response()

    def delete(self, request, notifications):
        for notification in notifications:
            notification.delete()
        msg = ngettext(
            '%(count)d notification deleted',
            '%(count)d notifications deleted', len(notifications)) \
            % {'count': len(notifications)}
        messages.success(request, msg)
        return self.get_success_response()
