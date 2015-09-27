from django.contrib import admin

from oscar.core.loading import get_model

Partner = get_model('partner', 'Partner')
StockRecord = get_model('partner', 'StockRecord')


class StockRecordAdmin(admin.ModelAdmin):
    list_display = ('product', 'partner', 'partner_sku', 'price_excl_tax',
                    'cost_price', 'num_in_stock')
    list_filter = ('partner',)


admin.site.register(Partner)
admin.site.register(StockRecord, StockRecordAdmin)
