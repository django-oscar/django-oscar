from django.contrib import admin

from oscar.services import import_module
models = import_module('order.models', ['Order', 'OrderNote', 'CommunicationEvent', 'CommunicationEventType',
                                        'BillingAddress', 'Batch', 'ShippingAddress', 'BatchLine',
                                        'BatchLinePrice', 'ShippingEvents', 'ShippingEventType', 
                                        'PaymentEvent', 'PaymentEventType', 'BatchLineAttribute'])

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

admin.site.register(models.Order)
admin.site.register(models.OrderNote, OrderNoteAdmin)
admin.site.register(models.CommunicationEvent)
admin.site.register(models.CommunicationEventType, CommunicationEventTypeAdmin)
admin.site.register(models.BillingAddress)
admin.site.register(models.Batch, BatchAdmin)
admin.site.register(models.ShippingAddress)
admin.site.register(models.BatchLine, BatchLineAdmin)
admin.site.register(models.BatchLinePrice)
admin.site.register(models.ShippingEvent)
admin.site.register(models.ShippingEventType, ShippingEventTypeAdmin)
admin.site.register(models.PaymentEvent)
admin.site.register(models.PaymentEventType, PaymentEventTypeAdmin)
admin.site.register(models.BatchLineAttribute)

