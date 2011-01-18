from django.contrib import admin
from oscar.stock.models import *

class StockRecordAdmin(admin.ModelAdmin):
    pass
    
admin.site.register(Partner)
admin.site.register(StockRecord, StockRecordAdmin)
