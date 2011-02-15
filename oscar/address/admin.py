from django.contrib import admin

from oscar.services import import_module
models = import_module('address.models', ['UserAddress', 'Country'])

admin.site.register(models.UserAddress)
admin.site.register(models.Country)
