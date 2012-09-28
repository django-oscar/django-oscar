from django.views import generic
from django.db.models import get_model
from django.contrib import messages
from django.utils.translation import ugettext_lazy as _
from django import http
from django.template import TemplateSyntaxError

from oscar.core.loading import get_class

CommunicationEventType = get_model('customer', 'CommunicationEventType')
CommunicationEventTypeForm = get_class('dashboard.communications.forms',
                                       'CommunicationEventTypeForm')
Dispatcher = get_class('customer.utils', 'Dispatcher')


class ListView(generic.ListView):
    model = CommunicationEventType
    template_name = 'dashboard/comms/list.html'
    context_object_name = 'commtypes'


class UpdateView(generic.UpdateView):
    model = CommunicationEventType
    form_class = CommunicationEventTypeForm
    template_name = 'dashboard/comms/detail.html'
    context_object_name = 'commtype'
    success_url = '.'

    def form_valid(self, form):
        if 'send_preview' in self.request.POST:
            return self.send_preview(form)
        messages.success(self.request, _("Email saved"))
        return super(UpdateView, self).form_valid(form)

    def send_preview(self, form):
        commtype = form.save(commit=False)
        commtype_ctx = {}
        ctx = super(UpdateView, self).get_context_data()
        ctx['form'] = form
        try:
            msgs = commtype.get_messages(commtype_ctx)
        except TemplateSyntaxError, e:
            form.errors['__all__'] = form.error_class([e.message])
            return self.render_to_response(ctx)

        dispatch = Dispatcher()
        dispatch.send_email_messages(
            form.cleaned_data['preview_email'], msgs)

        return self.render_to_response(ctx)
