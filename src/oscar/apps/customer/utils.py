import logging

from django.conf import settings
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import EmailMessage, EmailMultiAlternatives
from django.urls import reverse
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode

from oscar.core.loading import get_model


CommunicationEvent = get_model('order', 'CommunicationEvent')
Email = get_model('customer', 'Email')


class Dispatcher(object):
    def __init__(self, logger=None, mail_connection=None):
        if not logger:
            logger = logging.getLogger(__name__)
        self.logger = logger
        # Supply a mail_connection if you want the dispatcher to use that
        # instead of opening a new one.
        self.mail_connection = mail_connection

    # Public API methods

    def dispatch_direct_messages(self, recipient, messages):
        """
        Dispatch one-off messages to explicitly specified recipient.
        """
        if messages['subject'] and (messages['body'] or messages['html']):
            return self.send_email_messages(recipient, messages)

    def dispatch_order_messages(self, order, messages, event_type=None, **kwargs):
        """
        Dispatch order-related messages to the customer.
        """
        if order.is_anonymous:
            email = kwargs.get('email_address', order.guest_email)
            dispatched_messages = self.dispatch_anonymous_messages(email, messages)
        else:
            dispatched_messages = self.dispatch_user_messages(order.user, messages)

        self.create_communication_event(order, event_type, dispatched_messages)

    def dispatch_anonymous_messages(self, email, messages):
        dispatched_messages = {}
        if email:
            dispatched_messages['email'] = self.send_email_messages(email, messages), None
        return dispatched_messages

    def dispatch_user_messages(self, user, messages):
        """
        Send messages to a site user
        """
        dispatched_messages = {}
        if messages['subject'] and (messages['body'] or messages['html']):
            dispatched_messages['email'] = self.send_user_email_messages(user, messages)
        if messages['sms']:
            dispatched_messages['sms'] = self.send_text_message(user, messages['sms'])
        return dispatched_messages

    # Internal

    def create_communication_event(self, order, event_type, dispatched_messages):
        """
        Create order communications event for audit
        """
        if dispatched_messages and event_type is not None:
            CommunicationEvent._default_manager.create(order=order, event_type=event_type)

    def create_customer_email(self, user, messages, email):
        """
        Create Email instance in database for logging purposes.
        """
        # Is user is signed in, record the event for audit
        if email and user.is_authenticated:
            return Email._default_manager.create(user=user,
                                                 email=user.email,
                                                 subject=email.subject,
                                                 body_text=email.body,
                                                 body_html=messages['html'])

    def send_user_email_messages(self, user, messages):
        """
        Send message to the registered user / customer and collect data in database.
        """
        if not user.email:
            self.logger.warning("Unable to send email messages as user #%d has"
                                " no email address", user.id)
            return None, None

        email = self.send_email_messages(user.email, messages)
        return email, self.create_customer_email(user, messages, email)

    def send_email_messages(self, recipient, messages):
        """
        Send email to recipient, HTML attachment optional.
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

        if self.mail_connection:
            self.mail_connection.send_messages([email])
        else:
            email.send()

        return email

    def send_text_message(self, user, event_type):
        raise NotImplementedError


def get_password_reset_url(user, token_generator=default_token_generator):
    """
    Generate a password-reset URL for a given user
    """
    kwargs = {
        'token': token_generator.make_token(user),
        'uidb64': urlsafe_base64_encode(force_bytes(user.id)).decode(),
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
        local, host = clean_email.split('@')
        return local + '@' + host.lower()
    return clean_email
