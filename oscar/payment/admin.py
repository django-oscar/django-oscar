from django.contrib import admin

from oscar.services import import_module
models = import_module('payment.models', ['Source', 'Transaction', 'SourceType'])

class SourceAdmin(admin.ModelAdmin):
    list_display = ('order', 'type', 'allocation', 'amount_debited', 'reference')

admin.site.register(models.Source, SourceAdmin)
admin.site.register(models.SourceType)
admin.site.register(models.Transaction)
