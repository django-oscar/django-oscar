from django.contrib import admin

models = import_module('offer.models', ['ConditionalOffer', 'Condition', 'Benefit', 'Range',
                                        'Voucher'])

admin.site.register(models.ConditionalOffer)
admin.site.register(models.Condition)
admin.site.register(models.Benefit)
admin.site.register(models.Range)
admin.site.register(models.Voucher)
