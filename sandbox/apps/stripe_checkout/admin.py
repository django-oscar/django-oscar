from django.contrib import admin

from apps.stripe_checkout.models import StripeCheckout


@admin.register(StripeCheckout)
class StripeCheckoutAdmin(admin.ModelAdmin):
    list_display = ("order_number", "email", "amount", "currency", "status", "created")
    list_filter = ("status",)
    search_fields = ("order_number", "email", "session_id", "payment_intent")
    readonly_fields = [field.name for field in StripeCheckout._meta.fields]
