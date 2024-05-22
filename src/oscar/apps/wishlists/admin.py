from django.contrib import admin

from oscar.core.loading import get_model

WishList = get_model("wishlists", "WishList")
Line = get_model("wishlists", "Line")
WishListSharedEmail = get_model("wishlists", "WishListSharedEmail")


admin.site.register(WishList)
admin.site.register(Line)
admin.site.register(WishListSharedEmail)
