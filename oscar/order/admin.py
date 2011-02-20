from django.contrib import admin

from oscar.services import import_module
models = import_module('order.models', ['Order', 'OrderNote', 'CommunicationEvent', 'CommunicationEventType',
                                        'BillingAddress', 'Batch', 'ShippingAddress', 'BatchLine',
                                        'BatchLinePrice', 'ShippingEvent', 'ShippingEventType', 
                                        'PaymentEvent', 'PaymentEventType', 'BatchLineAttribute'])

class OrderAdmin(admin.ModelAdmin):
    list_display = ('number', 'total_incl_tax', 'site', 'user', 'billing_address', 'date_placed')
    readonly_fields = ('number', 'total_incl_tax', 'total_excl_tax', 'shipping_incl_tax', 'shipping_excl_tax')

class BatchAdmin(admin.ModelAdmin):
    list_display = ('order', 'partner', 'get_num_items')

class BatchLineAdmin(admin.ModelAdmin):
    list_display = ('batch', 'product', 'quantity')

class CommunicationEventTypeAdmin(admin.ModelAdmin):
    exclude = ('code',)

class ShippingEventTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'is_required', 'sequence_number')
    exclude = ('code',)
    
class PaymentEventTypeAdmin(admin.ModelAdmin):
    exclude = ('code',)
    
class OrderNoteAdmin(admin.ModelAdmin):
    exclude = ('user',)
    
    def save_model(self, request, obj, form, change):
        if not change:
            obj.user = request.user
        obj.save()

admin.site.register(models.Order, OrderAdmin)
admin.site.register(models.Batch, BatchAdmin)
admin.site.register(models.ShippingAddress)
admin.site.register(models.BatchLine, BatchLineAdmin)
admin.site.register(models.BatchLinePrice)
admin.site.register(models.ShippingEvent)
admin.site.register(models.ShippingEventType, ShippingEventTypeAdmin)
admin.site.register(models.PaymentEvent)
admin.site.register(models.PaymentEventType, PaymentEventTypeAdmin)
admin.site.register(models.BatchLineAttribute)

