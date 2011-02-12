from django.contrib import admin

from oscar.services import import_module
models = import_module('shipping.models', ['Method'])

admin.site.register(models.Method)
