from django.contrib import admin

from oscar.core.loading import import_module
models = import_module('partner.models', ['Partner', 'StockRecord'])

class StockRecordAdmin(admin.ModelAdmin):
    list_display = ('product', 'partner', 'partner_sku', 'price_excl_tax', 'cost_price', 'num_in_stock')
    list_filter = ('partner',)
    
admin.site.register(models.Partner)
admin.site.register(models.StockRecord, StockRecordAdmin)
