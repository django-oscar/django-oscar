from django.contrib import admin

from oscar.core.loading import get_model


class UserAddressAdmin(admin.ModelAdmin):
    readonly_fields = ('num_orders',)


class CountryAdmin(admin.ModelAdmin):
    search_fields = ('name',)


admin.site.register(get_model('address', 'useraddress'), UserAddressAdmin)
admin.site.register(get_model('address', 'country'), CountryAdmin)
