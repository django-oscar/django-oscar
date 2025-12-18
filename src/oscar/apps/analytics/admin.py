from django.contrib import admin

from oscar.core.loading import get_model


class ProductRecordAdmin(admin.ModelAdmin):
    list_display = ("product", "num_views", "num_basket_additions", "num_purchases")
    autocomplete_fields = ("product",)
    search_fields = ("product__title", "product__upc")


class UserProductViewAdmin(admin.ModelAdmin):
    list_display = ("user", "product", "date_created")
    autocomplete_fields = ("user", "product")
    search_fields = ("user__username", "user__email", "product__title", "product__upc")


class UserRecordAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "num_product_views",
        "num_basket_additions",
        "num_orders",
        "total_spent",
        "date_last_order",
    )
    autocomplete_fields = ("user",)
    search_fields = ("user__username", "user__email")


class UserSearchAdmin(admin.ModelAdmin):
    autocomplete_fields = ("user",)
    search_fields = ("user__username", "user__email", "query")


admin.site.register(get_model("analytics", "productrecord"), ProductRecordAdmin)
admin.site.register(get_model("analytics", "userrecord"), UserRecordAdmin)
admin.site.register(get_model("analytics", "usersearch"), UserSearchAdmin)
admin.site.register(get_model("analytics", "userproductview"), UserProductViewAdmin)
