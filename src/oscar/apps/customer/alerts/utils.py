import logging

from django.db.models import Max
from django.template import loader

from oscar.core.loading import get_class, get_model

ProductAlert = get_model("customer", "ProductAlert")
Product = get_model("catalogue", "Product")
Dispatcher = get_class("communication.utils", "Dispatcher")
Selector = get_class("partner.strategy", "Selector")

alerts_logger = logging.getLogger("oscar.alerts")


class AlertsDispatcher:
    """
    Dispatcher to send concrete product alerts related emails
    and notifications.
    """

    # Event codes
    PRODUCT_ALERT_EVENT_CODE = "PRODUCT_ALERT"
    PRODUCT_ALERT_CONFIRMATION_EVENT_CODE = "PRODUCT_ALERT_CONFIRMATION"

    def __init__(self, logger=None, mail_connection=None):
        self.dispatcher = Dispatcher(
            logger=logger or alerts_logger,
            mail_connection=mail_connection,
        )

    def get_queryset(self):
        return (
            Product.objects.browsable()
            .filter(productalert__status=ProductAlert.ACTIVE)
            .distinct()
        )

    def send_alerts(self):
        """
        Check all products with active product alerts for
        availability and send out email alerts when a product is
        available to buy.
        """
        products = self.get_queryset()
        self.dispatcher.logger.info(
            "Found %d products with active alerts", products.count()
        )
        for product in products:
            self.send_product_alert_email_for_user(product)

    def get_extra_context(self, alert, hurry_mode):
        return {
            "alert": alert,
            "hurry": hurry_mode,
        }

    def send_product_alert_email_for_user(self, product):
        """
        Check for notifications for this product and send email to users
        if the product is back in stock. Add a little 'hurry' note if the
        amount of in-stock items is less then the number of notifications.
        """
        stockrecords = product.stockrecords.all()
        num_stockrecords = len(stockrecords)
        if not num_stockrecords:
            return

        self.dispatcher.logger.info("Sending alerts for '%s'", product)
        alerts = ProductAlert.objects.filter(
            product_id__in=(product.id, product.parent_id),
            status=ProductAlert.ACTIVE,
        )

        # Determine 'hurry mode'
        if num_stockrecords == 1:
            num_in_stock = stockrecords[0].num_in_stock
        else:
            result = stockrecords.aggregate(max_in_stock=Max("num_in_stock"))
            num_in_stock = result["max_in_stock"]

        # 'hurry_mode' is false if 'num_in_stock' is None
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

            extra_context = self.get_extra_context(alert, hurry_mode)
            if alert.user:
                # Send a site notification
                num_notifications += 1
                self.notify_user_about_product_alert(alert.user, extra_context)

            messages = self.dispatcher.get_messages(
                self.PRODUCT_ALERT_EVENT_CODE, extra_context
            )

            if messages and messages["body"]:
                if alert.user:
                    user_messages_to_send.append((alert.user, messages))
                else:
                    messages_to_send.append((alert.get_email_address(), messages))
            alert.close()

        if messages_to_send or user_messages_to_send:
            for message in messages_to_send:
                self.dispatcher.dispatch_direct_messages(*message)
            for message in user_messages_to_send:
                self.dispatcher.dispatch_user_messages(*message)

        self.dispatcher.logger.info(
            "Sent %d notifications and %d messages",
            num_notifications,
            len(messages_to_send) + len(user_messages_to_send),
        )

    def send_product_alert_confirmation_email_for_user(self, alert, extra_context=None):
        """
        Send an alert confirmation email.
        """
        if extra_context is None:
            extra_context = {"alert": alert}
        messages = self.dispatcher.get_messages(
            self.PRODUCT_ALERT_CONFIRMATION_EVENT_CODE, extra_context
        )
        self.dispatcher.dispatch_direct_messages(alert.email, messages)

    def notify_user_about_product_alert(self, user, context):
        subj_tpl = loader.get_template("oscar/customer/alerts/message_subject.html")
        message_tpl = loader.get_template("oscar/customer/alerts/message.html")
        self.dispatcher.notify_user(
            user,
            subj_tpl.render(context).strip(),
            body=message_tpl.render(context).strip(),
        )
