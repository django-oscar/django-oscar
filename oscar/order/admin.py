from django.contrib import admin
from oscar.order.models import *

class BatchAdmin(admin.ModelAdmin):
    list_display = ('order', 'partner', 'get_num_items', 'shipping_method')

class BatchLineAdmin(admin.ModelAdmin):
    list_display = ('batch', 'product', 'quantity')

admin.site.register(Order)
admin.site.register(BillingAddress)
admin.site.register(Batch, BatchAdmin)
admin.site.register(ShippingAddress)
admin.site.register(BatchLine, BatchLineAdmin)
admin.site.register(BatchLinePrice)
admin.site.register(BatchLineEvent)
admin.site.register(BatchLineEventType)
admin.site.register(BatchLineAttribute)

