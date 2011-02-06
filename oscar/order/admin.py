from django.contrib import admin
from oscar.order.models import *

class BatchAdmin(admin.ModelAdmin):
    list_display = ('order', 'partner', 'get_num_items', 'shipping_method')

class BatchLineAdmin(admin.ModelAdmin):
    list_display = ('batch', 'product', 'quantity')

class CommunicationEventTypeAdmin(admin.ModelAdmin):
    exclude = ('code',)

class ShippingEventTypeAdmin(admin.ModelAdmin):
    exclude = ('code',)
    
class PaymentEventTypeAdmin(admin.ModelAdmin):
    exclude = ('code',)
    
class OrderNoteAdmin(admin.ModelAdmin):
    exclude = ('user',)
    
    def save_model(self, request, obj, form, change):
        if not change:
            obj.user = request.user
        obj.save()

admin.site.register(Order)
admin.site.register(OrderNote, OrderNoteAdmin)
admin.site.register(CommunicationEvent)
admin.site.register(CommunicationEventType, CommunicationEventTypeAdmin)
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

