from django.contrib import admin

from oscar.core.loading import get_model


class ProductRecordAdmin(admin.ModelAdmin):
    list_display = ("product", "num_views", "num_basket_additions", "num_purchases")


class UserProductViewAdmin(admin.ModelAdmin):
    list_display = ("user", "product", "date_created")


class UserRecordAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "num_product_views",
        "num_basket_additions",
        "num_orders",
        "total_spent",
        "date_last_order",
    )


admin.site.register(get_model("analytics", "productrecord"), ProductRecordAdmin)
admin.site.register(get_model("analytics", "userrecord"), UserRecordAdmin)
admin.site.register(get_model("analytics", "usersearch"))
admin.site.register(get_model("analytics", "userproductview"), UserProductViewAdmin)
