from django.conf import settings
from django.contrib import messages
from django.utils.html import strip_tags
from django.utils.timezone import now
from django.utils.translation import ugettext_lazy as _
from django.utils.translation import ungettext
from django.views import generic

from oscar.apps.customer.mixins import PageTitleMixin
from oscar.core.loading import get_model
from oscar.core.utils import redirect_to_referrer
from oscar.views.generic import BulkEditMixin

Notification = get_model('customer', 'Notification')


class NotificationListView(PageTitleMixin, generic.ListView):
    model = Notification
    template_name = 'customer/notifications/list.html'
    context_object_name = 'notifications'
    paginate_by = settings.OSCAR_NOTIFICATIONS_PER_PAGE
    page_title = _("Notifications")
    active_tab = 'notifications'

    def get_context_data(self, **kwargs):
        ctx = super(NotificationListView, self).get_context_data(**kwargs)
        ctx['list_type'] = self.list_type
        return ctx


class InboxView(NotificationListView):
    list_type = 'inbox'

    def get_queryset(self):
        qs = self.model._default_manager.filter(
            recipient=self.request.user,
            location=self.model.INBOX)
        # Mark unread notifications so they can be rendered differently...
        for obj in qs:
            if not obj.is_read:
                setattr(obj, 'is_new', True)
        # ...but then mark everything as read.
        self.mark_as_read(qs)
        return qs

    def mark_as_read(self, queryset):
        unread = queryset.filter(date_read=None)
        unread.update(date_read=now())


class ArchiveView(NotificationListView):
    list_type = 'archive'

    def get_queryset(self):
        return self.model._default_manager.filter(
            recipient=self.request.user,
            location=self.model.ARCHIVE)


class DetailView(PageTitleMixin, generic.DetailView):
    model = Notification
    template_name = 'customer/notifications/detail.html'
    context_object_name = 'notification'
    active_tab = 'notifications'

    def get_page_title(self):
        """Append subject to page title"""
        title = strip_tags(self.object.subject)
        return u'%s: %s' % (_('Notification'), title)

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
        return redirect_to_referrer(
            self.request, 'customer:notifications-inbox')

    def archive(self, request, notifications):
        for notification in notifications:
            notification.archive()
        msg = ungettext(
            '%(count)d notification archived',
            '%(count)d notifications archived', len(notifications)) \
            % {'count': len(notifications)}
        messages.success(request, msg)
        return self.get_success_response()

    def delete(self, request, notifications):
        for notification in notifications:
            notification.delete()
        msg = ungettext(
            '%(count)d notification deleted',
            '%(count)d notifications deleted', len(notifications)) \
            % {'count': len(notifications)}
        messages.success(request, msg)
        return self.get_success_response()
