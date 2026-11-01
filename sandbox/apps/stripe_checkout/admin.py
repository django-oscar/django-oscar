from django.contrib import admin

from apps.stripe_checkout.models import StripeCheckout, StripeCustomer


@admin.register(StripeCheckout)
class StripeCheckoutAdmin(admin.ModelAdmin):
    list_display = ("order_number", "email", "amount", "currency", "status", "created")
    list_filter = ("status",)
    search_fields = ("order_number", "email", "session_id", "payment_intent")
    readonly_fields = [field.name for field in StripeCheckout._meta.fields]


@admin.register(StripeCustomer)
class StripeCustomerAdmin(admin.ModelAdmin):
    list_display = ("customer_id", "user", "livemode", "created")
    list_filter = ("livemode",)
    search_fields = ("customer_id", "user__email")
    readonly_fields = [field.name for field in StripeCustomer._meta.fields]
