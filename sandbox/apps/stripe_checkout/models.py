from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _


class StripeCheckout(models.Model):
    """A Stripe Checkout Session paying a frozen basket; the order is placed
    once Stripe confirms the payment (webhook or status poll)"""

    OPEN, PAID, EXPIRED, CANCELED = "open", "paid", "expired", "canceled"
    STATUS_CHOICES = (
        (OPEN, _("Waiting for payment")),
        (PAID, _("Paid")),
        (EXPIRED, _("Expired")),
        (CANCELED, _("Canceled")),
    )

    session_id = models.CharField(_("Stripe session"), max_length=255, unique=True)
    basket = models.ForeignKey(
        "basket.Basket", on_delete=models.CASCADE, related_name="stripe_checkouts"
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="stripe_checkouts",
    )
    email = models.EmailField(_("Email"))
    # ShippingAddress fields, the country as its ISO 3166-1 alpha-2 code
    shipping_address = models.JSONField(_("Shipping address"))
    shipping_code = models.CharField(_("Shipping method"), max_length=128)
    order_number = models.CharField(_("Order number"), max_length=128)
    amount = models.DecimalField(_("Amount"), decimal_places=2, max_digits=12)
    currency = models.CharField(_("Currency"), max_length=12)
    status = models.CharField(
        _("Status"), max_length=16, choices=STATUS_CHOICES, default=OPEN
    )
    payment_intent = models.CharField(_("Payment intent"), max_length=255, blank=True)
    order = models.ForeignKey(
        "order.Order",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="stripe_checkouts",
    )
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("-created",)
        verbose_name = _("Stripe checkout")
        verbose_name_plural = _("Stripe checkouts")

    def __str__(self):
        return "%s (%s)" % (self.order_number, self.status)
