import logging

from django.conf import settings
from django.contrib.auth import login as auth_login
from django.contrib.auth import authenticate
from django.contrib.sites.models import get_current_site

from oscar.apps.customer.signals import user_registered
from oscar.core.compat import get_user_model
from oscar.core.loading import get_class, get_model

User = get_user_model()
CommunicationEventType = get_model('customer', 'CommunicationEventType')
Dispatcher = get_class('customer.utils', 'Dispatcher')

logger = logging.getLogger('oscar.customer')


class PageTitleMixin(object):
    """
    Passes page_title and active_tab into context, which makes it quite useful
    for the accounts views.

    Dynamic page titles are possible by overriding get_page_title.
    """
    page_title = None
    active_tab = None

    # Use a method that can be overridden and customised
    def get_page_title(self):
        return self.page_title

    def get_context_data(self, **kwargs):
        ctx = super(PageTitleMixin, self).get_context_data(**kwargs)
        ctx.setdefault('page_title', self.get_page_title())
        ctx.setdefault('active_tab', self.active_tab)
        return ctx


class RegisterUserMixin(object):
    communication_type_code = 'REGISTRATION'

    def register_user(self, form):
        """
        Create a user instance and send a new registration email (if configured
        to).
        """
        user = form.save()

        # Raise signal robustly (we don't want exceptions to crash the request
        # handling).
        user_registered.send_robust(
            sender=self, request=self.request, user=user)

        if getattr(settings, 'OSCAR_SEND_REGISTRATION_EMAIL', True):
            self.send_registration_email(user)

        # We have to authenticate before login
        try:
            user = authenticate(
                username=user.email,
                password=form.cleaned_data['password1'])
        except User.MultipleObjectsReturned:
            # Handle race condition where the registration request is made
            # multiple times in quick succession.  This leads to both requests
            # passing the uniqueness check and creating users (as the first one
            # hasn't committed when the second one runs the check).  We retain
            # the first one and deactivate the dupes.
            logger.warning(
                'Multiple users with identical email address and password'
                'were found. Marking all but one as not active.')
            # As this section explicitly deals with the form being submitted
            # twice, this is about the only place in Oscar where we don't
            # ignore capitalisation when looking up an email address.
            # We might otherwise accidentally mark unrelated users as inactive
            users = User.objects.filter(email=user.email)
            user = users[0]
            for u in users[1:]:
                u.is_active = False
                u.save()

        auth_login(self.request, user)

        return user

    def send_registration_email(self, user):
        code = self.communication_type_code
        ctx = {'user': user,
               'site': get_current_site(self.request)}
        messages = CommunicationEventType.objects.get_and_render(
            code, ctx)
        if messages and messages['body']:
            Dispatcher().dispatch_user_messages(user, messages)
