from django.contrib import admin

from oscar.services import import_module
models = import_module('order.models', ['Order', 'OrderNote', 'CommunicationEvent', 'CommunicationEventType',
                                        'BillingAddress', 'ShippingAddress', 'Line',
                                        'LinePrice', 'ShippingEvent', 'ShippingEventType', 
                                        'PaymentEvent', 'PaymentEventType', 'LineAttribute'])

class OrderAdmin(admin.ModelAdmin):
    list_display = ('number', 'total_incl_tax', 'site', 'user', 'billing_address', 'date_placed')
    readonly_fields = ('number', 'total_incl_tax', 'total_excl_tax', 'shipping_incl_tax', 'shipping_excl_tax')

class LineAdmin(admin.ModelAdmin):
    list_display = ('order', 'product', 'quantity')

class LinePriceAdmin(admin.ModelAdmin):
    list_display = ('order', 'line', 'price_incl_tax', 'quantity')

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
admin.site.register(models.ShippingAddress)
admin.site.register(models.Line, LineAdmin)
admin.site.register(models.LinePrice, LinePriceAdmin)
admin.site.register(models.ShippingEvent)
admin.site.register(models.ShippingEventType, ShippingEventTypeAdmin)
admin.site.register(models.PaymentEvent)
admin.site.register(models.PaymentEventType, PaymentEventTypeAdmin)
admin.site.register(models.LineAttribute)

