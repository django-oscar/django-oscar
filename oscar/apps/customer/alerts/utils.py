import logging

from django.core import mail
from django.conf import settings
from django.template import loader, Context
from django.contrib.sites.models import Site
from django.db.models import get_model

from oscar.apps.customer.notifications import services

ProductAlert = get_model('customer', 'ProductAlert')
Product = get_model('catalogue', 'Product')

logger = logging.getLogger(__file__)


def send_alerts():
    """
    Send out product alerts
    """
    products = Product.objects.filter(
        productalert__status=ProductAlert.ACTIVE
    ).distinct()
    logger.info("Found %d products with active alerts", products.count())
    for product in products:
        if product.is_available_to_buy:
            send_product_alerts(product)


def send_alert_confirmation(alert):
    """
    Send an alert confirmation email.
    """
    ctx = Context({
        'alert': alert,
        'site': Site.objects.get_current(),
    })
    subject_tpl = loader.get_template('customer/alerts/emails/confirmation_subject.txt')
    body_tpl = loader.get_template('customer/alerts/emails/confirmation_body.txt')
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
    if not product.has_stockrecord:
        return
    num_in_stock = product.stockrecord.num_in_stock
    if num_in_stock == 0:
        return

    logger.info("Sending alerts for '%s'", product)
    alerts = ProductAlert.objects.filter(
        product=product,
        status=ProductAlert.ACTIVE,
    )
    hurry_mode = alerts.count() < product.stockrecord.num_in_stock

    # Load templates
    message_tpl = loader.get_template('customer/alerts/message.html')
    email_subject_tpl = loader.get_template('customer/alerts/emails/alert_subject.txt')
    email_body_tpl = loader.get_template('customer/alerts/emails/alert_body.txt')

    emails = []
    num_notifications = 0
    for alert in alerts:
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
    connection = mail.get_connection()
    connection.open()
    connection.send_messages(emails)
    connection.close()

    logger.info("Sent %d notifications and %d emails", num_notifications, len(emails))