from django.contrib import admin

from oscar.core.loading import import_module
import_module('customer.models', ['Email'], locals())

admin.site.register(Email)



