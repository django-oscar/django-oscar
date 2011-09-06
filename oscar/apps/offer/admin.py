from django.contrib import admin

from oscar.core.loading import import_module
import_module('offer.models', ['ConditionalOffer', 'Condition', 'Benefit', 'Range'], locals())


class ConditionAdmin(admin.ModelAdmin):
    list_display = ('type', 'value', 'range')


class BenefitAdmin(admin.ModelAdmin):
    list_display = ('__unicode__', 'type', 'value', 'range')
    
    
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
