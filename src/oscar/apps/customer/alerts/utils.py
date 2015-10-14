import logging

from django.conf import settings
from django.contrib.sites.models import Site
from django.core import mail
from django.db.models import Max
from django.template import Context, loader

from oscar.apps.customer.notifications import services
from oscar.core.loading import get_class, get_model

ProductAlert = get_model('customer', 'ProductAlert')
Product = get_model('catalogue', 'Product')
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
    ctx = Context({
        'alert': alert,
        'site': Site.objects.get_current(),
    })
    subject_tpl = loader.get_template('customer/alerts/emails/'
                                      'confirmation_subject.txt')
    body_tpl = loader.get_template('customer/alerts/emails/'
                                   'confirmation_body.txt')
    mail.send_mail(
        subject_tpl.render(ctx).strip(),
        body_tpl.render(ctx),
        settings.OSCAR_FROM_EMAIL,
        [alert.email],
    )


def send_product_alerts(product):
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
    num_alerts = alerts.count()
    if num_stockrecords == 1:
        num_in_stock = stockrecords[0].num_in_stock
        # hurry_mode is false if num_in_stock is None
        hurry_mode = num_in_stock is not None and num_alerts < num_in_stock
    else:
        result = stockrecords.aggregate(max_in_stock=Max('num_in_stock'))
        hurry_mode = result['max_in_stock'] is not None and \
            num_alerts < result['max_in_stock']

    # Load templates
    message_tpl = loader.get_template('customer/alerts/message.html')
    email_subject_tpl = loader.get_template('customer/alerts/emails/'
                                            'alert_subject.txt')
    email_body_tpl = loader.get_template('customer/alerts/emails/'
                                         'alert_body.txt')

    emails = []
    num_notifications = 0
    selector = Selector()
    for alert in alerts:
        # Check if the product is available to this user
        strategy = selector.strategy(user=alert.user)
        data = strategy.fetch_for_product(product)
        if not data.availability.is_available_to_buy:
            continue

        ctx = Context({
            'alert': alert,
            'site': Site.objects.get_current(),
            'hurry': hurry_mode,
        })
        if alert.user:
            # Send a site notification
            num_notifications += 1
            services.notify_user(alert.user, message_tpl.render(ctx))

        # Build email and add to list
        emails.append(
            mail.EmailMessage(
                email_subject_tpl.render(ctx).strip(),
                email_body_tpl.render(ctx),
                settings.OSCAR_FROM_EMAIL,
                [alert.get_email_address()],
            )
        )
        alert.close()

    # Send all emails in one go to prevent multiple SMTP
    # connections to be opened
    if emails:
        connection = mail.get_connection()
        connection.open()
        connection.send_messages(emails)
        connection.close()

    logger.info("Sent %d notifications and %d emails", num_notifications,
                len(emails))
