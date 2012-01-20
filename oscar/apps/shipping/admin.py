from django.contrib import admin

from oscar.apps.shipping.methods import OrderAndItemCharges, WeightBand


class MethodAdmin(admin.ModelAdmin):
    exclude = ('code',)
    list_display = ('name', 'description', 'price_per_order', 'price_per_item', 'free_shipping_threshold')


admin.site.register(OrderAndItemCharges, MethodAdmin)
admin.site.register(WeightBand)
