import logging

from django import http
from django.contrib import messages
from django.contrib.auth.models import User
from django.template.loader import get_template
from django.urls import reverse
from django.views import generic

from apps.gateway import forms
from oscar.apps.customer.forms import generate_username
from oscar.core.loading import get_class

Dispatcher = get_class('communication.utils', 'Dispatcher')

logger = logging.getLogger('gateway')


class GatewayView(generic.FormView):
    template_name = 'gateway/form.html'
    form_class = forms.GatewayForm

    def form_valid(self, form):
        real_email = form.cleaned_data['email']
        username = generate_username()
        password = generate_username()
        email = 'dashboard-user-%s@oscarcommerce.com' % username

        user = self.create_dashboard_user(username, email, password)
        self.send_confirmation_email(real_email, user, password)
        logger.info("Created dashboard user #%d for %s",
                    user.id, real_email)

        messages.success(
            self.request,
            "The credentials for a dashboard user have been sent to %s" % real_email)
        return http.HttpResponseRedirect(reverse('gateway'))

    def create_dashboard_user(self, username, email, password):
        user = User.objects.create_user(username, email, password)
        user.is_staff = True
        user.save()
        return user

    def send_confirmation_email(self, real_email, user, password):
        msgs = {
            'subject': 'Dashboard access to Oscar sandbox',
            'body': get_template('gateway/email.txt').render({
                'email': user.email, 'password': password})
        }
        Dispatcher().send_email_messages(
            real_email, msgs, from_email='blackhole@latest.oscarcommerce.com')
