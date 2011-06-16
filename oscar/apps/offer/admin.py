from django.contrib import admin

from oscar.core.loading import import_module
import_module('offer.models', ['ConditionalOffer', 'Condition', 'Benefit', 'Range',
                                        'Voucher', 'VoucherApplication'], locals())

class ConditionAdmin(admin.ModelAdmin):
    list_display = ('type', 'value', 'range')

class BenefitAdmin(admin.ModelAdmin):
    list_display = ('__unicode__', 'type', 'value', 'range')
    
class VoucherAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'usage', 'num_basket_additions', 'num_orders', 'total_discount')    
    readonly_fields = ('num_basket_additions', 'num_orders', 'total_discount')
    fieldsets = (
        (None, {
            'fields': ('name', 'code', 'usage', 'start_date', 'end_date')
        }),
        ('Benefit', {
            'fields': ('offers',)
        }),
        ('Usage', {
            'fields': ('num_basket_additions', 'num_orders', 'total_discount')
        }),
        
    )
    
class VoucherApplicationAdmin(admin.ModelAdmin):
    list_display = ('voucher', 'user', 'order', 'date_created')
    readonly_fields = ('voucher', 'user', 'order')        
    
class ConditionalOfferAdmin(admin.ModelAdmin):
    list_display = ('name', 'offer_type', 'start_date', 'end_date', 'condition', 'benefit', 'total_discount')
    list_filter = ('offer_type',)
    readonly_fields = ('total_discount',)
    fieldsets = (
        (None, {
            'fields': ('name', 'description', 'offer_type', 'condition', 'benefit', 'start_date', 'end_date', 'priority')
        }),
        ('Usage', {
            'fields': ('total_discount',)
        }),
    )

admin.site.register(ConditionalOffer, ConditionalOfferAdmin)
admin.site.register(Condition, ConditionAdmin)
admin.site.register(Benefit, BenefitAdmin)
admin.site.register(Range)
admin.site.register(Voucher, VoucherAdmin)
admin.site.register(VoucherApplication, VoucherApplicationAdmin)
