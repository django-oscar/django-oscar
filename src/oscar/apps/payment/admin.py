from django.contrib import admin

from oscar.core.loading import get_model

Source = get_model("payment", "Source")
Transaction = get_model("payment", "Transaction")
SourceType = get_model("payment", "SourceType")
Bankcard = get_model("payment", "Bankcard")


class SourceAdmin(admin.ModelAdmin):
    list_display = (
        "order",
        "source_type",
        "amount_allocated",
        "amount_debited",
        "balance",
        "reference",
    )
    list_filter = ("source_type",)
    raw_id_fields = ("order",)
    search_fields = ("order__number",)


class BankcardAdmin(admin.ModelAdmin):
    list_display = ("number", "card_type", "expiry_month")


class TransactionAdmin(admin.ModelAdmin):
    raw_id_fields = ("source",)
    search_fields = ("source__order__number",)


admin.site.register(Source, SourceAdmin)
admin.site.register(SourceType)
admin.site.register(Transaction, TransactionAdmin)
admin.site.register(Bankcard, BankcardAdmin)
