from django.contrib import admin

from oscar.core.loading import get_model

OrderAndItemCharges = get_model("shipping", "OrderAndItemCharges")
WeightBand = get_model("shipping", "WeightBand")
WeightBased = get_model("shipping", "WeightBased")


class OrderChargesAdmin(admin.ModelAdmin):
    filter_horizontal = ("countries",)
    list_display = (
        "name",
        "description",
        "price_per_order",
        "price_per_item",
        "free_shipping_threshold",
    )


class WeightBandInline(admin.TabularInline):
    model = WeightBand


class WeightBasedAdmin(admin.ModelAdmin):
    filter_horizontal = ("countries",)
    inlines = [WeightBandInline]


admin.site.register(OrderAndItemCharges, OrderChargesAdmin)
admin.site.register(WeightBased, WeightBasedAdmin)
