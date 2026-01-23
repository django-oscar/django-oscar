from django.contrib import admin

from oscar.core.loading import get_model


class UserAddressAdmin(admin.ModelAdmin):
    readonly_fields = (
        "num_orders_as_billing_address",
        "num_orders_as_shipping_address",
    )
    autocomplete_fields = ("user",)
    search_fields = (
        "user__username",
        "user__email",
        "line1",
        "line2",
        "line3",
        "line4",
        "state",
        "postcode",
        "phone_number",
        "code",
    )


class CountryAdmin(admin.ModelAdmin):
    list_display = ["__str__", "display_order"]
    list_filter = ["is_shipping_country"]
    search_fields = ["name", "printable_name", "iso_3166_1_a2", "iso_3166_1_a3"]


admin.site.register(get_model("address", "useraddress"), UserAddressAdmin)
admin.site.register(get_model("address", "country"), CountryAdmin)
