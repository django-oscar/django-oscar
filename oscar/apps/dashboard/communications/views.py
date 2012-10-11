from django.views import generic
from django.db.models import get_model
from django.contrib import messages
from django.shortcuts import get_object_or_404
from django.utils.translation import ugettext_lazy as _
from django.contrib.sites.models import get_current_site
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

    def get_object(self, **kwargs):
        return get_object_or_404(self.model,
                                 code=self.kwargs['code'].upper())

    def form_valid(self, form):
        if 'send_preview' in self.request.POST:
            return self.send_preview(form)
        if 'show_preview' in self.request.POST:
            return self.show_preview(form)
        messages.success(self.request, _("Email saved"))
        return super(UpdateView, self).form_valid(form)

    def show_preview(self, form):
        commtype = form.save(commit=False)
        commtype_ctx = {}
        commtype_ctx = {'user': self.request.user,
                        'site': get_current_site(self.request)}
        ctx = super(UpdateView, self).get_context_data()
        ctx['form'] = form
        try:
            msgs = commtype.get_messages(commtype_ctx)
        except TemplateSyntaxError, e:
            form.errors['__all__'] = form.error_class([e.message])
            return self.render_to_response(ctx)

        ctx['show_preview'] = True
        ctx['preview'] = msgs
        return self.render_to_response(ctx)

    def send_preview(self, form):
        commtype = form.save(commit=False)
        commtype_ctx = {}
        commtype_ctx = {'user': self.request.user,
                        'site': get_current_site(self.request)}
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
