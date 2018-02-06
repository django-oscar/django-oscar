import logging
import warnings

from django.contrib.sites.models import Site
from django.core import mail
from django.db.models import Max
from django.template import TemplateDoesNotExist, loader

from oscar.apps.customer.notifications import services
from oscar.core.loading import get_class, get_model
from oscar.utils.deprecation import RemovedInOscar20Warning

CommunicationEventType = get_model('customer', 'CommunicationEventType')
ProductAlert = get_model('customer', 'ProductAlert')
Product = get_model('catalogue', 'Product')
Dispatcher = get_class('customer.utils', 'Dispatcher')
Selector = get_class('partner.strategy', 'Selector')

logger = logging.getLogger('oscar.alerts')


def send_alerts():
    """
    Send out product alerts
    """
    products = Product.objects.filter(
        productalert__status=ProductAlert.ACTIVE
    ).distinct()
    logger.info("Found %d products with active alerts", products.count())
    for product in products:
        send_product_alerts(product)


def send_alert_confirmation(alert):
    """
    Send an alert confirmation email.
    """
    ctx = {
        'alert': alert,
        'site': Site.objects.get_current(),
    }

    # For backwards compability, we check if the old (non-communication-event)
    # templates exist, and use them if they do.
    # This will be removed in Oscar 2.0
    try:
        subject_tpl = loader.get_template('customer/alerts/emails/'
                                          'confirmation_subject.txt')
        body_tpl = loader.get_template('customer/alerts/emails/'
                                       'confirmation_body.txt')
        warnings.warn(
            "Product alert notifications now use the CommunicationEvent. "
            "Move '{}' to '{}', and '{}' to '{}'".format(
                'customer/alerts/emails/confirmation_subject.txt',
                'customer/emails/commtype_product_alert_confirmation_subject.txt',
                'customer/alerts/emails/confirmation_body.txt',
                'customer/emails/commtype_product_alert_confirmation_body.txt',
            ),
            category=RemovedInOscar20Warning, stacklevel=2
        )

        messages = {
            'subject': subject_tpl.render(ctx).strip(),
            'body': body_tpl.render(ctx),
            'html': '',
            'sms': '',
        }
    except TemplateDoesNotExist:
        code = 'PRODUCT_ALERT_CONFIRMATION'
        messages = CommunicationEventType.objects.get_and_render(code, ctx)

    if messages and messages['body']:
        Dispatcher().dispatch_direct_messages(alert.email, messages)


def send_product_alerts(product):   # noqa C901 too complex
    """
    Check for notifications for this product and send email to users
    if the product is back in stock. Add a little 'hurry' note if the
    amount of in-stock items is less then the number of notifications.
    """
    stockrecords = product.stockrecords.all()
    num_stockrecords = len(stockrecords)
    if not num_stockrecords:
        return

    logger.info("Sending alerts for '%s'", product)
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

    # For backwards compability, we check if the old (non-communication-event)
    # templates exist, and use them if they do.
    # This will be removed in Oscar 2.0
    try:
        email_subject_tpl = loader.get_template('customer/alerts/emails/'
                                                'alert_subject.txt')
        email_body_tpl = loader.get_template('customer/alerts/emails/'
                                             'alert_body.txt')

        use_deprecated_templates = True
        warnings.warn(
            "Product alert notifications now use the CommunicationEvent. "
            "Move '{}' to '{}', and '{}' to '{}'".format(
                'customer/alerts/emails/alert_subject.txt',
                'customer/emails/commtype_product_alert_subject.txt',
                'customer/alerts/emails/alert_body.txt',
                'customer/emails/commtype_product_alert_body.txt',
            ),
            category=RemovedInOscar20Warning, stacklevel=2
        )

    except TemplateDoesNotExist:
        code = 'PRODUCT_ALERT'
        try:
            event_type = CommunicationEventType.objects.get(code=code)
        except CommunicationEventType.DoesNotExist:
            event_type = CommunicationEventType.objects.model(code=code)
        use_deprecated_templates = False

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

        ctx = {
            'alert': alert,
            'site': Site.objects.get_current(),
            'hurry': hurry_mode,
        }
        if alert.user:
            # Send a site notification
            num_notifications += 1
            subj_tpl = loader.get_template('customer/alerts/message_subject.html')
            message_tpl = loader.get_template('customer/alerts/message.html')
            services.notify_user(
                alert.user,
                subj_tpl.render(ctx).strip(),
                body=message_tpl.render(ctx).strip()
            )

        # Build message and add to list
        if use_deprecated_templates:
            messages = {
                'subject': email_subject_tpl.render(ctx).strip(),
                'body': email_body_tpl.render(ctx),
                'html': '',
                'sms': '',
            }
        else:
            messages = event_type.get_messages(ctx)

        if messages and messages['body']:
            if alert.user:
                user_messages_to_send.append(
                    (alert.user, messages)
                )
            else:
                messages_to_send.append(
                    (alert.get_email_address(), messages)
                )
        alert.close()

    # Send all messages using one SMTP connection to avoid opening lots of them
    if messages_to_send or user_messages_to_send:
        connection = mail.get_connection()
        connection.open()
        disp = Dispatcher(mail_connection=connection)
        for message in messages_to_send:
            disp.dispatch_direct_messages(*message)
        for message in user_messages_to_send:
            disp.dispatch_user_messages(*message)
        connection.close()

    logger.info("Sent %d notifications and %d messages", num_notifications,
                len(messages_to_send) + len(user_messages_to_send))
