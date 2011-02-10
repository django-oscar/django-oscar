from django.contrib import admin

from oscar.services import import_module
models = import_module('payment.models', ['Source', 'Transaction'])

admin.site.register(models.Source)
admin.site.register(models.Transaction)
