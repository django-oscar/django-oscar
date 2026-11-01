from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class StripeCheckoutConfig(AppConfig):
    name = "apps.stripe_checkout"
    label = "stripe_checkout"
    verbose_name = _("Stripe Checkout")
    default_auto_field = "django.db.models.AutoField"
