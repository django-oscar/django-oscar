from django.contrib import admin

from oscar.core.loading import get_model


class UserAddressAdmin(admin.ModelAdmin):
    readonly_fields = ('num_orders_as_billing_address', 'num_orders_as_shipping_address')


class CountryAdmin(admin.ModelAdmin):
    list_display = [
        '__str__',
        'display_order'
    ]
    list_filter = [
        'is_shipping_country'
    ]
    search_fields = [
        'name',
        'printable_name',
        'iso_3166_1_a2',
        'iso_3166_1_a3'
    ]


admin.site.register(get_model('address', 'useraddress'), UserAddressAdmin)
admin.site.register(get_model('address', 'country'), CountryAdmin)
