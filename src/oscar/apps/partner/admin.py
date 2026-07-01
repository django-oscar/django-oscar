from django.contrib import admin

from oscar.core.loading import get_model

Partner = get_model("partner", "Partner")
StockRecord = get_model("partner", "StockRecord")


class PartnerAdmin(admin.ModelAdmin):
    list_display = ("name", "code")
    search_fields = ("name", "code")


class StockRecordAdmin(admin.ModelAdmin):
    list_display = ("product", "partner", "partner_sku", "price", "num_in_stock")
    list_filter = ("partner",)
    autocomplete_fields = ("product", "partner")
    search_fields = ("partner__name", "product__title", "product__upc")


admin.site.register(Partner, PartnerAdmin)
admin.site.register(StockRecord, StockRecordAdmin)
