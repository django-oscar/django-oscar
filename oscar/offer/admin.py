from django.contrib import admin

from oscar.services import import_module
models = import_module('offer.models', ['ConditionalOffer', 'Condition', 'Benefit', 'Range',
                                        'Voucher', 'VoucherApplication'])

class ConditionAdmin(admin.ModelAdmin):
    list_display = ('type', 'value', 'range')

class BenefitAdmin(admin.ModelAdmin):
    list_display = ('__unicode__', 'type', 'value', 'range')
    
class VoucherAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'usage', 'num_basket_additions', 'num_orders', 'total_discount')    
    
class ConditionalOfferAdmin(admin.ModelAdmin):
    list_display = ('name', 'offer_type', 'start_date', 'end_date', 'condition', 'benefit')
    list_filter = ('offer_type',)

admin.site.register(models.ConditionalOffer, ConditionalOfferAdmin)
admin.site.register(models.Condition, ConditionAdmin)
admin.site.register(models.Benefit, BenefitAdmin)
admin.site.register(models.Range)
admin.site.register(models.Voucher, VoucherAdmin)
admin.site.register(models.VoucherApplication)
