from django.contrib import admin

from oscar.services import import_module
models = import_module('stock.models', ['Partner', 'StockRecord'])

class StockRecordAdmin(admin.ModelAdmin):
    pass
    
admin.site.register(models.Partner)
admin.site.register(models.StockRecord, StockRecordAdmin)
