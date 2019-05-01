import logging
import six

from django.conf import settings
from django.contrib.sites.models import Site
from django.core.mail import EmailMessage, EmailMultiAlternatives
from django.db.models import Max
from django.template import loader

from oscar.core.loading import get_class, get_model


CommunicationEvent = get_model('order', 'CommunicationEvent')
CommunicationEventType = get_model('communication', 'CommunicationEventType')
Email = get_model('communication', 'Email')
Notification = get_model('communication', 'Notification')
ProductAlert = get_model('customer', 'ProductAlert')
Selector = get_class('partner.strategy', 'Selector')


class Dispatcher(object):

    # Event codes
    REGISTRATION_EVENT_CODE = 'REGISTRATION'
    PASSWORD_RESET_EVENT_CODE = 'PASSWORD_RESET'
    PASSWORD_CHANGED_EVENT_CODE = 'PASSWORD_CHANGED'
    EMAIL_CHANGED_EVENT_CODE = 'EMAIL_CHANGED'
    PRODUCT_ALERT_EVENT_CODE = 'PRODUCT_ALERT'
    PRODUCT_ALERT_CONFIRMATION_EVENT_CODE = 'PRODUCT_ALERT_CONFIRMATION'
    ORDER_PLACED_EVENT_CODE = 'ORDER_PLACED'

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

    def dispatch_order_messages(self, order, messages, event_code, attachments=None, **kwargs):
        """
        Dispatch order-related messages to the customer.
        """
        self.logger.info(
            "Order #%s - sending %s messages", order.number, event_code)
        if order.is_anonymous:
            email = kwargs.get('email_address', order.guest_email)
            dispatched_messages = self.dispatch_anonymous_messages(email, messages, attachments)
        else:
            dispatched_messages = self.dispatch_user_messages(order.user, messages, attachments)

        try:
            event_type = CommunicationEventType.objects.get(code=event_code)
        except CommunicationEventType.DoesNotExist:
            event_type = None

        self.create_communication_event(order, event_type, dispatched_messages)

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

    def send_user_email_messages(self, user, messages, attachments=None):
        """
        Send message to the registered user / customer and collect data in database.
        """
        if not user.email:
            self.logger.warning("Unable to send email messages as user #%d has"
                                " no email address", user.id)
            return None, None

        email = self.send_email_messages(user.email, messages, attachments=attachments)

        if getattr(settings, 'OSCAR_SAVE_SENT_EMAILS_TO_DB', True):
            self.create_customer_email(user, messages, email)

        return email

    def send_email_messages(self, recipient_email, messages, from_email=None, attachments=None):
        """
        Send email to recipient, HTML attachment optional.
        """
        if hasattr(settings, 'OSCAR_FROM_EMAIL'):
            from_email = settings.OSCAR_FROM_EMAIL

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
        content_attachments = []
        file_attachments = []
        if attachments is not None:
            for attachment in attachments:
                if isinstance(attachment, six.string_types):
                    # Here `attachment` is path to file from instance of `FileField` based fields
                    file_attachments.append(attachment)
                else:
                    # Here attachment is one of:
                    #   * instance of `MIMEBase` (from `email.mime.base`)
                    #   * list `[filename, content, mimetype]`
                    content_attachments.append(attachment)

        return content_attachments, file_attachments

    def get_base_context(self):
        """
        Return context that common for all emails
        """
        return {'site': Site.objects.get_current()}

    def get_messages(self, event_code, extra_context=None):
        """
        Return rendered messages
        """
        context = self.get_base_context()
        if extra_context is not None:
            context.update(extra_context)
        msgs = CommunicationEventType.objects.get_and_render(event_code, context)
        return msgs

    # Concrete email sending

    def send_registration_email_for_user(self, user, extra_context):
        messages = self.get_messages(
            self.REGISTRATION_EVENT_CODE, extra_context)
        self.dispatch_user_messages(user, messages)

    def send_password_reset_email_for_user(self, user, extra_context):
        messages = self.get_messages(
            self.PASSWORD_RESET_EVENT_CODE, extra_context)
        self.dispatch_user_messages(user, messages)

    def send_password_changed_email_for_user(self, user, extra_context):
        messages = self.get_messages(
            self.PASSWORD_CHANGED_EVENT_CODE, extra_context)
        self.dispatch_user_messages(user, messages)

    def send_email_changed_email_for_user(self, user, extra_context):
        messages = self.get_messages(
            self.EMAIL_CHANGED_EVENT_CODE, extra_context)
        self.dispatch_user_messages(user, messages)

    def send_order_placed_email_for_user(self, order, extra_context, attachments=None):
        event_code = self.ORDER_PLACED_EVENT_CODE
        messages = self.get_messages(event_code, extra_context)
        self.dispatch_order_messages(order, messages, event_code, attachments=attachments)

    def notify_user_about_product_alert(self, user, context):
        subj_tpl = loader.get_template('customer/alerts/message_subject.html')
        message_tpl = loader.get_template('customer/alerts/message.html')
        self.notify_user(
            user,
            subj_tpl.render(context).strip(),
            body=message_tpl.render(context).strip()
        )

    def send_product_alert_email_for_user(self, product):  # noqa: C901 too complex
        """
        Check for notifications for this product and send email to users
        if the product is back in stock. Add a little 'hurry' note if the
        amount of in-stock items is less then the number of notifications.
        """
        stockrecords = product.stockrecords.all()
        num_stockrecords = len(stockrecords)
        if not num_stockrecords:
            return

        self.logger.info("Sending alerts for '%s'", product)
        alerts = ProductAlert.objects.filter(
            product_id__in=(product.id, product.parent_id),
            status=ProductAlert.ACTIVE,
        )

        # Determine 'hurry mode'
        if num_stockrecords == 1:
            num_in_stock = stockrecords[0].num_in_stock
        else:
            result = stockrecords.aggregate(max_in_stock=Max('num_in_stock'))
            num_in_stock = result['max_in_stock']

        # hurry_mode is false if num_in_stock is None
        hurry_mode = num_in_stock is not None and alerts.count() > num_in_stock

        messages_to_send = []
        user_messages_to_send = []
        num_notifications = 0
        selector = Selector()
        for alert in alerts:
            # Check if the product is available to this user
            strategy = selector.strategy(user=alert.user)
            data = strategy.fetch_for_product(product)
            if not data.availability.is_available_to_buy:
                continue

            extra_context = {
                'alert': alert,
                'hurry': hurry_mode,
            }
            if alert.user:
                # Send a site notification
                num_notifications += 1
                self.notify_user_about_product_alert(alert.user, extra_context)

            messages = self.get_messages(self.PRODUCT_ALERT_EVENT_CODE, extra_context)

            if messages and messages['body']:
                if alert.user:
                    user_messages_to_send.append((alert.user, messages))
                else:
                    messages_to_send.append((alert.get_email_address(), messages))
            alert.close()

        if messages_to_send or user_messages_to_send:
            for message in messages_to_send:
                self.dispatch_direct_messages(*message)
            for message in user_messages_to_send:
                self.dispatch_user_messages(*message)

        self.logger.info(
            "Sent %d notifications and %d messages",
            num_notifications, len(messages_to_send) + len(user_messages_to_send)
        )

    def send_product_alert_confirmation_email_for_user(self, alert, extra_context=None):
        """
        Send an alert confirmation email.
        """
        if extra_context is None:
            extra_context = {'alert': alert}
        messages = self.get_messages(self.PRODUCT_ALERT_CONFIRMATION_EVENT_CODE, extra_context)
        self.dispatch_direct_messages(alert.email, messages)
