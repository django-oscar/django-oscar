from django.contrib import admin

from oscar.services import import_module
models = import_module('offer.models', ['ConditionalOffer', 'Condition', 'Benefit', 'Range'])

class ConditionAdmin(admin.ModelAdmin):
    list_display = ('type', 'value', 'range')

class BenefitAdmin(admin.ModelAdmin):
    list_display = ('__unicode__', 'type', 'value', 'range')
    
class ConditionalOfferAdmin(admin.ModelAdmin):
    list_display = ('name', 'start_date', 'end_date', 'condition', 'benefit')

admin.site.register(models.ConditionalOffer, ConditionalOfferAdmin)
admin.site.register(models.Condition, ConditionAdmin)
admin.site.register(models.Benefit, BenefitAdmin)
admin.site.register(models.Range)
