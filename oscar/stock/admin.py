from django.contrib import admin
from oscar.stock.models import *

class StockRecordAdmin(admin.ModelAdmin):
    exclude = ('num_allocated',)

admin.site.register(Partner)
admin.site.register(StockRecord, StockRecordAdmin)
