from django.contrib import admin

from oscar.core.loading import get_model

Order = get_model("order", "Order")
OrderNote = get_model("order", "OrderNote")
OrderStatusChange = get_model("order", "OrderStatusChange")
CommunicationEvent = get_model("order", "CommunicationEvent")
BillingAddress = get_model("order", "BillingAddress")
ShippingAddress = get_model("order", "ShippingAddress")
Line = get_model("order", "Line")
LinePrice = get_model("order", "LinePrice")
ShippingEvent = get_model("order", "ShippingEvent")
ShippingEventType = get_model("order", "ShippingEventType")
PaymentEvent = get_model("order", "PaymentEvent")
PaymentEventType = get_model("order", "PaymentEventType")
PaymentEventQuantity = get_model("order", "PaymentEventQuantity")
LineAttribute = get_model("order", "LineAttribute")
OrderDiscount = get_model("order", "OrderDiscount")
Surcharge = get_model("order", "Surcharge")


class LineInline(admin.TabularInline):
    model = Line
    extra = 0
    autocomplete_fields = ("product",)
    raw_id_fields = ("stockrecord",)

    def get_fields(self, request, obj=None):
        fields = super().get_fields(request, obj)
        priority = ("product", "quantity", "line_price_incl_tax")

        return list(priority) + [f for f in fields if f not in priority]


class OrderAdmin(admin.ModelAdmin):
    raw_id_fields = [
        "billing_address",
        "shipping_address",
    ]
    autocomplete_fields = ("user",)
    list_display = (
        "number",
        "total_incl_tax",
        "site",
        "user",
        "billing_address",
        "date_placed",
    )
    readonly_fields = (
        "number",
        "basket",
        "total_incl_tax",
        "total_excl_tax",
        "shipping_incl_tax",
        "shipping_excl_tax",
    )
    inlines = [LineInline]
    search_fields = ("number", "user__username", "user__email")


class LineAdmin(admin.ModelAdmin):
    list_display = ("order", "product", "stockrecord", "quantity")
    raw_id_fields = ("stockrecord", "order")
    autocomplete_fields = ("product",)
    search_fields = (
        "order__number",
        "product__title",
        "product__upc",
        "order__user__email",
    )


class LinePriceAdmin(admin.ModelAdmin):
    list_display = ("order", "line", "price_incl_tax", "quantity")
    search_fields = ("order__number",)
    raw_id_fields = ("line", "order")


class ShippingEventTypeAdmin(admin.ModelAdmin):
    list_display = ("name",)


class PaymentEventQuantityInline(admin.TabularInline):
    model = PaymentEventQuantity
    extra = 0
    raw_id_fields = ("line",)


class PaymentEventAdmin(admin.ModelAdmin):
    list_display = (
        "order",
        "event_type",
        "amount",
        "num_affected_lines",
        "date_created",
    )
    inlines = [PaymentEventQuantityInline]
    raw_id_fields = ("order", "shipping_event")
    search_fields = ("order__number",)
    list_filter = ("event_type",)


class PaymentEventTypeAdmin(admin.ModelAdmin):
    pass


class OrderDiscountAdmin(admin.ModelAdmin):
    readonly_fields = (
        "order",
        "category",
        "offer_id",
        "offer_name",
        "voucher_id",
        "voucher_code",
        "amount",
    )
    list_display = ("order", "category", "offer", "voucher", "voucher_code", "amount")
    search_fields = ("order__number", "offer_name", "voucher_code")


class SurchargeAdmin(admin.ModelAdmin):
    raw_id_fields = ("order",)
    search_fields = ("order__number",)


class OrderNoteAdmin(admin.ModelAdmin):
    search_fields = ("order__number",)
    raw_id_fields = ("order",)
    autocomplete_fields = ("user",)


class OrderStatusAdmin(admin.ModelAdmin):
    search_fields = ("order__number",)
    raw_id_fields = ("order",)


class ShippingAddressAdmin(admin.ModelAdmin):
    search_fields = ("search_text", "code")


class ShippingEventAdmin(admin.ModelAdmin):
    search_fields = ("order__number",)
    raw_id_fields = ("order",)


class LineAttributeAdmin(admin.ModelAdmin):
    search_fields = ("line__order__number",)
    readonly_fields = ("line",)
    list_filter = ("option",)


class CommunicationEventAdmin(admin.ModelAdmin):
    search_fields = ("order__number", "order__user__email")
    list_filter = ("event_type",)
    raw_id_fields = ("order",)


class BillingAddressAdmin(admin.ModelAdmin):
    search_fields = ("order__user__email", "search_text", "code")


admin.site.register(Order, OrderAdmin)
admin.site.register(OrderNote, OrderNoteAdmin)
admin.site.register(OrderStatusChange, OrderStatusAdmin)
admin.site.register(ShippingAddress, ShippingAddressAdmin)
admin.site.register(Line, LineAdmin)
admin.site.register(LinePrice, LinePriceAdmin)
admin.site.register(ShippingEvent, ShippingEventAdmin)
admin.site.register(ShippingEventType, ShippingEventTypeAdmin)
admin.site.register(PaymentEvent, PaymentEventAdmin)
admin.site.register(PaymentEventType, PaymentEventTypeAdmin)
admin.site.register(LineAttribute, LineAttributeAdmin)
admin.site.register(OrderDiscount, OrderDiscountAdmin)
admin.site.register(CommunicationEvent, CommunicationEventAdmin)
admin.site.register(BillingAddress, BillingAddressAdmin)
admin.site.register(Surcharge, SurchargeAdmin)
