import datetime

from django.core import mail
from django.conf import settings
from django.template import loader, Context
from django.contrib.sites.models import Site
from django.utils.translation import ugettext as _

from oscar.core.loading import get_class

# use get_class instead of get_model as this module get imported
# in the models module of notification. That means models are not
# available at this point in time.
StockRecord = get_class('partner.models', 'StockRecord')
ProductNotification = get_class('catalogue.notification.models',
                                'ProductNotification')


def create_email_from_context(email, template, context):
    """
    Create ``EmailMessage`` with message body composed as HTML from
    *template* rendered with *context*. The email address to send the
    message to is provided by *email*. The content subtype of the
    message is set to ``html``.

    Returns a ``EmailMessage`` instance.
    """
    subject = _("[Product Notification] Product '%(title)s' back in stock!")
    subject = subject % {'title': context['product'].title}

    msg = mail.EmailMessage(
        template.render(context),
        subject,
        settings.OSCAR_FROM_EMAIL,
        [email],
    )
    msg.content_subtype = "html",
    return msg


def send_email_notifications_for_product(product):
    """
    Check for notifications for this product and send email to users
    if the product is back in stock. Add a little 'hurry' note if the
    amount of in-stock items is less then the number of notifications.
    """
    notifications = ProductNotification.objects.filter(
        product=product,
        status=ProductNotification.ACTIVE,
    )

    # ignore the rest if no notifications for this stockrecord
    if not len(notifications):
        return

    # add a hurry disclaimer if less products in stock then
    # notifications requested
    context = Context({
        'product': product,
        'site': Site.objects.get(pk=getattr(settings, 'SITE_ID', 1)),
        'hurry': len(notifications) <= product.stockrecord.num_in_stock,
    })

    template_file = getattr(settings, 'OSCAR_NOTIFICATION_EMAIL_TEMPLATE',
                            'notification/notification_email.html')
    template = loader.get_template(template_file)

    email_messages = []
    # generate personalised emails for registered users first
    for notification in notifications.exclude(user=None):
        context['user'] = notification.user
        email_messages.append(create_email_from_context(
            notification.get_notification_email(),
            template,
            context
        ))

    # generate the same email for all anonymous users
    for notification in notifications.filter(user=None):
        email_messages.append(create_email_from_context(
            notification.get_notification_email(),
            template,
            context
        ))

    # send all emails in one go to prevent multiple SMTP
    # connections to be opened
    connection = mail.get_connection()
    connection.send_messages(email_messages)
    connection.close()

    # set the notified date for all notifications and deactivate them
    for notification in notifications:
        notification.status = ProductNotification.INACTIVE
        notification.date_notified = datetime.datetime.now()
        notification.save()
