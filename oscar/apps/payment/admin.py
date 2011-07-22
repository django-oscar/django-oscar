from django.contrib import admin

from oscar.core.loading import import_module
models = import_module('payment.models', ['Source', 'Transaction', 'SourceType'])

class SourceAdmin(admin.ModelAdmin):
    list_display = ('order', 'source_type', 'amount_allocated', 'amount_debited', 'balance', 'reference')


admin.site.register(models.Source, SourceAdmin)
admin.site.register(models.SourceType)
admin.site.register(models.Transaction)
