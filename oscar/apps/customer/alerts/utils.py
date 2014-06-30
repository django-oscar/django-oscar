import logging

from django.core import mail
from django.conf import settings
from django.template import loader, Context
from django.contrib.sites.models import Site
from django.db.models import Max

from oscar.apps.customer.notifications import services
from oscar.core.loading import get_class, get_model

ProductAlert = get_model('customer', 'ProductAlert')
Product = get_model('catalogue', 'Product')
Selector = get_class('partner.strategy', 'Selector')

module_logger = logging.getLogger('oscar.alerts')


def send_alert_confirmation(alert):
    """
    Send a confirmation email for the given alert instance.
    """
    module_logger.info("Sending alert confirmation email to %s for alert #%d",
                       alert.email, alert.id)
    ctx = Context({
        'alert': alert,
        'site': Site.objects.get_current(),
    })
    subject_tpl = loader.get_template(
        'customer/alerts/emails/confirmation_subject.txt')
    body_tpl = loader.get_template(
        'customer/alerts/emails/confirmation_body.txt')
    mail.send_mail(
        subject_tpl.render(ctx).strip(),
        body_tpl.render(ctx),
        settings.OSCAR_FROM_EMAIL,
        [alert.email],
    )


def send_alerts(logger):
    """
    Send out product alerts for any products that have have active
    alerts.
    """
    products = Product.objects.filter(
        productalert__status=ProductAlert.ACTIVE
    ).distinct()
    logger.info("Found %d products with active alerts", products.count())
    for product in products:
        send_product_alerts(product, logger)


def send_product_alerts(product, logger):
    """
    Check for notifications for this product and send email to users
    if the product is back in stock. Add a little 'hurry' note if the
    amount of in-stock items is less then the number of notifications.
    """
    stockrecords = product.stockrecords.all()
    num_stockrecords = len(stockrecords)
    if not num_stockrecords:
        logger.info("Product '%s' has no stockrecords, skipping", product)
        return

    alerts = ProductAlert.objects.filter(
        product=product,
        status=ProductAlert.ACTIVE,
    )
    logger.info("Found %d alerts for '%s'", alerts.count(), product)

    # Determine 'hurry mode'
    num_alerts = alerts.count()
    if num_stockrecords == 1:
        num_in_stock = stockrecords[0].num_in_stock
        # hurry_mode is false if num_in_stock is None
        hurry_mode = num_in_stock is not None and num_alerts < num_in_stock
    else:
        # When multiple stockrecords, we don't know exactly which stockrecord
        # corresponds to which user and so we look at the most conservative
        # case where all alerts correspond to the same stockrecord. This
        # avoids the possibility of false positives.
        result = stockrecords.aggregate(max_in_stock=Max('num_in_stock'))
        hurry_mode = result['max_in_stock'] is not None and \
            num_alerts < result['max_in_stock']

    # Load templates
    message_tpl = loader.get_template('customer/alerts/message.html')
    email_subject_tpl = loader.get_template(
        'customer/alerts/emails/' 'alert_subject.txt')
    email_body_tpl = loader.get_template(
        'customer/alerts/emails/' 'alert_body.txt')

    emails = []
    num_notifications = 0
    selector = Selector()
    for alert in alerts:
        # Check if the product is available to this user
        strategy = selector.strategy(user=alert.user)
        data = strategy.fetch_for_product(product)
        if not data.availability.is_available_to_buy:
            logger.debug("Product %s is not available to user #%d",
                         product, alert.user.id)
            continue

        ctx = Context({
            'alert': alert,
            'site': Site.objects.get_current(),
            'hurry': hurry_mode,
        })
        if alert.user:
            # Send a site notification
            logger.debug("Sending site notification to user #%d",
                         alert.user.id)
            num_notifications += 1
            services.notify_user(alert.user, message_tpl.render(ctx))

        # Build email and add to list
        logger.debug("Sending email notification to user #%d",
                     alert.user.id)
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

    logger.info(
        "Sent %d notifications and %d emails", num_notifications, len(emails))


def delete_unconfirmed_alerts(threshold_date, logger):
    """
    Delete alerts that are still unconfirmed and were created earlier than the
    passed threshold date.
    """
    logger.info('Deleting unconfirmed alerts older than %s',
                threshold_date.strftime("%Y-%m-%d %H:%M"))
    qs = ProductAlert.objects.filter(
        status=ProductAlert.UNCONFIRMED,
        date_created__lt=threshold_date
    )
    logger.info("Found %d stale alerts to delete", qs.count())
    qs.delete()
