from django.contrib import admin

from oscar.core.loading import get_model

WishList = get_model("wishlists", "WishList")
Line = get_model("wishlists", "Line")
WishListSharedEmail = get_model("wishlists", "WishListSharedEmail")


class WishListAdmin(admin.ModelAdmin):
    list_display = ("name", "owner", "date_created", "visibility")
    list_filter = ("visibility",)
    autocomplete_fields = ("owner",)
    search_fields = ("name", "owner__username", "owner__email")


class LineAdmin(admin.ModelAdmin):
    list_display = ("wishlist", "product", "quantity")
    autocomplete_fields = ("wishlist", "product")
    search_fields = ("wishlist__name", "product__title", "product__upc")


admin.site.register(WishList, WishListAdmin)
admin.site.register(Line, LineAdmin)
admin.site.register(WishListSharedEmail)
