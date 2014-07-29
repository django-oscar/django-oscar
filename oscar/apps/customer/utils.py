import logging

import django
from django.core.mail import EmailMessage, EmailMultiAlternatives
from django.core.urlresolvers import reverse
from django.conf import settings
from django.contrib.auth.tokens import default_token_generator

from oscar.core.loading import get_model

Email = get_model('customer', 'Email')


class Dispatcher(object):
    def __init__(self, logger=None):
        if not logger:
            logger = logging.getLogger(__name__)
        self.logger = logger

    # Public API methods

    def dispatch_direct_messages(self, recipient, messages):
        """
        Dispatch one-off messages to explicitly specified recipient(s).
        """
        if messages['subject'] and messages['body']:
            self.send_email_messages(recipient, messages)

    def dispatch_user_messages(self, user, messages):
        """
        Send messages to a site user
        """
        if messages['subject'] and (messages['body'] or messages['html']):
            self.send_user_email_messages(user, messages)
        if messages['sms']:
            self.send_text_message(user, messages['sms'])

    # Internal

    def send_user_email_messages(self, user, messages):
        """
        Sends message to the registered user / customer and collects data in
        database
        """
        if not user.email:
            self.logger.warning("Unable to send email messages as user #%d has"
                                " no email address", user.id)
            return

        email = self.send_email_messages(user.email, messages)

        # Is user is signed in, record the event for audit
        if email and user.is_authenticated():
            Email._default_manager.create(user=user,
                                          subject=email.subject,
                                          body_text=email.body,
                                          body_html=messages['html'])

    def send_email_messages(self, recipient, messages):
        """
        Plain email sending to the specified recipient
        """
        if hasattr(settings, 'OSCAR_FROM_EMAIL'):
            from_email = settings.OSCAR_FROM_EMAIL
        else:
            from_email = None

        # Determine whether we are sending a HTML version too
        if messages['html']:
            email = EmailMultiAlternatives(messages['subject'],
                                           messages['body'],
                                           from_email=from_email,
                                           to=[recipient])
            email.attach_alternative(messages['html'], "text/html")
        else:
            email = EmailMessage(messages['subject'],
                                 messages['body'],
                                 from_email=from_email,
                                 to=[recipient])
        self.logger.info("Sending email to %s" % recipient)
        email.send()

        return email

    def send_text_message(self, user, event_type):
        raise NotImplementedError


def get_password_reset_url(user, token_generator=default_token_generator):
    """
    Generate a password-reset URL for a given user
    """
    kwargs = {'token': token_generator.make_token(user)}
    if django.VERSION < (1, 6):
        from django.utils.http import int_to_base36
        kwargs['uidb36'] = int_to_base36(user.id)
    else:
        from django.utils.http import urlsafe_base64_encode
        from django.utils.encoding import force_bytes
        kwargs['uidb64'] = urlsafe_base64_encode(force_bytes(user.id))
    return reverse('password-reset-confirm', kwargs=kwargs)


def normalise_email(email):
    """
    The local part of an email address is case-sensitive, the domain part
    isn't.  This function lowercases the host and should be used in all email
    handling.
    """
    clean_email = email.strip()
    if '@' in clean_email:
        local, host = clean_email.split('@')
        return local + '@' + host.lower()
    return clean_email
