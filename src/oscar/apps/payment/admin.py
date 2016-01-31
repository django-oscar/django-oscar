from django.contrib import admin

from oscar.core.loading import get_model

Source = get_model('payment', 'Source')
Transaction = get_model('payment', 'Transaction')
SourceType = get_model('payment', 'SourceType')
Bankcard = get_model('payment', 'Bankcard')


class SourceAdmin(admin.ModelAdmin):
    list_display = ('order', 'source_type', 'amount_allocated',
                    'amount_debited', 'balance', 'reference')


class BankcardAdmin(admin.ModelAdmin):
    list_display = ('number', 'card_type', 'expiry_month')


admin.site.register(Source, SourceAdmin)
admin.site.register(SourceType)
admin.site.register(Transaction)
admin.site.register(Bankcard, BankcardAdmin)
