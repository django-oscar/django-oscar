from django.contrib import admin
from oscar.order.models import *

class BatchAdmin(admin.ModelAdmin):
    list_display = ('order', 'partner', 'get_num_items', 'shipping_method')

class BatchLineAdmin(admin.ModelAdmin):
    list_display = ('batch', 'product', 'quantity')

class OrderEventTypeAdmin(admin.ModelAdmin):
    exclude = ('code',)

class ShippingEventTypeAdmin(admin.ModelAdmin):
    exclude = ('code',)
    
class PaymentEventTypeAdmin(admin.ModelAdmin):
    exclude = ('code',)

admin.site.register(Order)
admin.site.register(OrderEvent)
admin.site.register(OrderEventType, OrderEventTypeAdmin)
admin.site.register(BillingAddress)
admin.site.register(Batch, BatchAdmin)
admin.site.register(ShippingAddress)
admin.site.register(BatchLine, BatchLineAdmin)
admin.site.register(BatchLinePrice)
admin.site.register(ShippingEvent)
admin.site.register(ShippingEventType, ShippingEventTypeAdmin)
admin.site.register(PaymentEvent)
admin.site.register(PaymentEventType, PaymentEventTypeAdmin)
admin.site.register(BatchLineAttribute)

