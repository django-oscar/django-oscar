from django.contrib import admin
from django.db.models import get_model

Order = get_model('order', 'Order')
OrderNote = get_model('order', 'OrderNote')
CommunicationEvent = get_model('order', 'CommunicationEvent')
BillingAddress = get_model('order', 'BillingAddress')
ShippingAddress = get_model('order', 'ShippingAddress')
Line = get_model('order', 'Line')
LinePrice = get_model('order', 'LinePrice')
ShippingEvent = get_model('order', 'ShippingEvent')
ShippingEventType = get_model('order', 'ShippingEventType')
PaymentEvent = get_model('order', 'PaymentEvent')
PaymentEventType = get_model('order', 'PaymentEventType')
LineAttribute = get_model('order', 'LineAttribute')
OrderDiscount = get_model('order', 'OrderDiscount')


class OrderAdmin(admin.ModelAdmin):
    raw_id_fields = ['user','billing_address','shipping_address', ]
    list_display = ('number', 'total_incl_tax', 'site', 'user', 'billing_address', 'date_placed')
    readonly_fields = ('number', 'total_incl_tax', 'total_excl_tax', 'shipping_incl_tax', 'shipping_excl_tax')


class LineAdmin(admin.ModelAdmin):
    list_display = ('order', 'product', 'quantity')


class LinePriceAdmin(admin.ModelAdmin):
    list_display = ('order', 'line', 'price_incl_tax', 'quantity')


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
        
        
class OrderDiscountAdmin(admin.ModelAdmin):
    readonly_fields = ('order' ,'offer_id', 'voucher_id', 'voucher_code', 'amount')
    list_display = ('order', 'offer', 'voucher', 'voucher_code', 'amount')
    

admin.site.register(Order, OrderAdmin)
admin.site.register(OrderNote, OrderNoteAdmin)
admin.site.register(ShippingAddress)
admin.site.register(Line, LineAdmin)
admin.site.register(LinePrice, LinePriceAdmin)
admin.site.register(ShippingEvent)
admin.site.register(ShippingEventType, ShippingEventTypeAdmin)
admin.site.register(PaymentEvent)
admin.site.register(PaymentEventType, PaymentEventTypeAdmin)
admin.site.register(LineAttribute)
admin.site.register(OrderDiscount, OrderDiscountAdmin)
admin.site.register(CommunicationEvent)
