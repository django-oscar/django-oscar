from django.contrib import admin

from oscar.core.loading import import_module
import_module('address.models', ['UserAddress', 'Country'], locals())

admin.site.register(UserAddress)
admin.site.register(Country)
