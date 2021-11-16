import logging

from django.conf import settings
from django.contrib.sites.models import Site
from django.core.mail import EmailMessage, EmailMultiAlternatives

from oscar.core.loading import get_model

CommunicationEventType = get_model('communication', 'CommunicationEventType')
Email = get_model('communication', 'Email')
Notification = get_model('communication', 'Notification')


class Dispatcher(object):

    def __init__(self, logger=None, mail_connection=None):
        if not logger:
            logger = logging.getLogger(__name__)
        self.logger = logger
        # Supply a mail_connection if you want the dispatcher to use that
        # instead of opening a new one.
        self.mail_connection = mail_connection

    # Public API methods

    def dispatch_direct_messages(self, recipient_email, messages, attachments=None):
        """
        Dispatch one-off messages to explicitly specified recipient email.
        """
        if messages['subject'] and (messages['body'] or messages['html']):
            return self.send_email_messages(recipient_email, messages, attachments=attachments)

    def dispatch_anonymous_messages(self, email, messages, attachments=None):
        dispatched_messages = {}
        if email:
            dispatched_messages['email'] = self.send_email_messages(email, messages, attachments=attachments), None
        return dispatched_messages

    def dispatch_user_messages(self, user, messages, attachments=None):
        """
        Send messages to a site user
        """
        dispatched_messages = {}
        if messages['subject'] and (messages['body'] or messages['html']):
            dispatched_messages['email'] = self.send_user_email_messages(user, messages, attachments)
        if messages['sms']:
            dispatched_messages['sms'] = self.send_text_message(user, messages['sms'])
        return dispatched_messages

    def notify_user(self, user, subject, **kwargs):
        """
        Send a simple notification to a user
        """
        Notification.objects.create(recipient=user, subject=subject, **kwargs)

    def notify_users(self, users, subject, **kwargs):
        """
        Send a simple notification to an iterable of users
        """
        for user in users:
            self.notify_user(user, subject, **kwargs)

    # Internal

    def create_email(self, user, messages, email):
        """
        Create ``Email`` instance in database for logging purposes.
        """
        if email and user.is_authenticated:
            return Email.objects.create(
                user=user,
                email=user.email,
                subject=email.subject,
                body_text=email.body,
                body_html=messages['html'],
            )

    def send_user_email_messages(self, user, messages, attachments=None):
        """
        Send message to the registered user / customer and collect data in database.
        """
        if not user.email:
            self.logger.warning("Unable to send email messages as user #%d has"
                                " no email address", user.id)
            return None

        email = self.send_email_messages(user.email, messages, attachments=attachments)

        if settings.OSCAR_SAVE_SENT_EMAILS_TO_DB:
            self.create_email(user, messages, email)

        return email

    def send_email_messages(self, recipient_email, messages, from_email=None, attachments=None):
        """
        Send email to recipient, HTML attachment optional.
        """
        from_email = from_email or settings.OSCAR_FROM_EMAIL

        content_attachments, file_attachments = self.prepare_attachments(attachments)

        # Determine whether we are sending a HTML version too
        if messages['html']:
            email = EmailMultiAlternatives(
                messages['subject'],
                messages['body'],
                from_email=from_email,
                to=[recipient_email],
                attachments=content_attachments,
            )
            email.attach_alternative(messages['html'], "text/html")
        else:
            email = EmailMessage(
                messages['subject'],
                messages['body'],
                from_email=from_email,
                to=[recipient_email],
                attachments=content_attachments,
            )
        for attachment in file_attachments:
            email.attach_file(attachment)

        self.logger.info("Sending email to %s" % recipient_email)

        if self.mail_connection:
            self.mail_connection.send_messages([email])
        else:
            email.send()

        return email

    def send_text_message(self, user, event_type):
        raise NotImplementedError

    def prepare_attachments(self, attachments):
        """
        Two types of attachments can be attached to emails:

            * "Content" attachment is one of:
                * instance of ``MIMEBase`` (from ``email.mime.base``);
                * list ``[filename, content, mimetype]``;

            * "File" attachment is a path to file from an instance of
              ``FileField`` based fields.

        "Content" and "file" attachments attached to emails differently.
        """
        content_attachments = []
        file_attachments = []
        if attachments is not None:
            for attachment in attachments:
                if isinstance(attachment, str):
                    file_attachments.append(attachment)
                else:
                    content_attachments.append(attachment)

        return content_attachments, file_attachments

    def get_base_context(self, **kwargs):
        """
        Return context that is common to all emails
        """
        request = kwargs.get("request")
        return dict(kwargs, site=Site.objects.get_current(request))

    def get_messages(self, event_code, extra_context=None):
        """
        Return rendered messages
        """
        if extra_context is None:
            extra_context = {}
        context = self.get_base_context(**extra_context)

        msgs = CommunicationEventType.objects.get_and_render(event_code, context)
        return msgs
