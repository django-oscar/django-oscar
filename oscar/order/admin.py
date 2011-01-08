from django.contrib import admin
from oscar.order.models import *

class BatchAdmin(admin.ModelAdmin):
    list_display = ('order', 'partner', 'num_items', 'delivery_method')

class BatchItemAdmin(admin.ModelAdmin):
    list_display = ('batch', 'product', 'price_incl_tax', 'payment_status', 'shipping_status')

admin.site.register(Order)
admin.site.register(BillingAddress)
admin.site.register(Batch, BatchAdmin)
admin.site.register(DeliveryAddress)
admin.site.register(BatchItem, BatchItemAdmin)
