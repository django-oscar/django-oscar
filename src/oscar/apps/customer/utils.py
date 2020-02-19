from django.contrib.auth.tokens import default_token_generator
from django.urls import reverse
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode

from oscar.core.loading import get_class

Dispatcher = get_class('communication.utils', 'Dispatcher')
Selector = get_class('partner.strategy', 'Selector')


class CustomerDispatcher:
    """
    Dispatcher to send concrete customer related emails.
    """

    # Event codes
    REGISTRATION_EVENT_CODE = 'REGISTRATION'
    PASSWORD_RESET_EVENT_CODE = 'PASSWORD_RESET'
    PASSWORD_CHANGED_EVENT_CODE = 'PASSWORD_CHANGED'
    EMAIL_CHANGED_EVENT_CODE = 'EMAIL_CHANGED'

    def __init__(self, logger=None, mail_connection=None):
        self.dispatcher = Dispatcher(logger=logger, mail_connection=mail_connection)

    def send_registration_email_for_user(self, user, extra_context):
        messages = self.dispatcher.get_messages(self.REGISTRATION_EVENT_CODE, extra_context)
        self.dispatcher.dispatch_user_messages(user, messages)

    def send_password_reset_email_for_user(self, user, extra_context):
        messages = self.dispatcher.get_messages(self.PASSWORD_RESET_EVENT_CODE, extra_context)
        self.dispatcher.dispatch_user_messages(user, messages)

    def send_password_changed_email_for_user(self, user, extra_context):
        messages = self.dispatcher.get_messages(self.PASSWORD_CHANGED_EVENT_CODE, extra_context)
        self.dispatcher.dispatch_user_messages(user, messages)

    def send_email_changed_email_for_user(self, user, extra_context):
        messages = self.dispatcher.get_messages(
            self.EMAIL_CHANGED_EVENT_CODE, extra_context)
        self.dispatcher.dispatch_user_messages(user, messages)


def get_password_reset_url(user, token_generator=default_token_generator):
    """
    Generate a password-reset URL for a given user
    """
    kwargs = {
        'token': token_generator.make_token(user),
        'uidb64': urlsafe_base64_encode(force_bytes(user.id)),
    }
    return reverse('password-reset-confirm', kwargs=kwargs)


def normalise_email(email):
    """
    The local part of an email address is case-sensitive, the domain part
    isn't.  This function lowercases the host and should be used in all email
    handling.
    """
    clean_email = email.strip()
    if '@' in clean_email:
        local, host = clean_email.rsplit('@', 1)
        return local + '@' + host.lower()
    return clean_email
