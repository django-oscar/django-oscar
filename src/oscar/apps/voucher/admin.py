from django.contrib import admin

from oscar.core.loading import get_model

Voucher = get_model("voucher", "Voucher")
VoucherApplication = get_model("voucher", "VoucherApplication")


class VoucherAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "code",
        "usage",
        "num_basket_additions",
        "num_orders",
        "total_discount",
    )
    readonly_fields = ("num_basket_additions", "num_orders", "total_discount")
    fieldsets = (
        (None, {"fields": ("name", "code", "usage", "start_datetime", "end_datetime")}),
        ("Benefit", {"fields": ("offers",)}),
        ("Usage", {"fields": ("num_basket_additions", "num_orders", "total_discount")}),
    )


class VoucherApplicationAdmin(admin.ModelAdmin):
    list_display = ("voucher", "user", "order", "date_created")
    readonly_fields = ("voucher", "user", "order")


admin.site.register(Voucher, VoucherAdmin)
admin.site.register(VoucherApplication, VoucherApplicationAdmin)
