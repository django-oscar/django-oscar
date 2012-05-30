from django.contrib import admin
from django.db.models import get_model
Source = get_model('payment', 'Source')
Transaction = get_model('payment', 'Transaction')
SourceType = get_model('payment', 'SourceType')


class SourceAdmin(admin.ModelAdmin):
    list_display = ('order', 'source_type', 'amount_allocated', 'amount_debited', 'balance', 'reference')


admin.site.register(Source, SourceAdmin)
admin.site.register(SourceType)
admin.site.register(Transaction)
