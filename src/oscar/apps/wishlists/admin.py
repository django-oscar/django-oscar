from django.contrib import admin

from oscar.core.loading import get_model

WishList = get_model('wishlists', 'WishList')
Line = get_model('wishlists', 'Line')


admin.site.register(WishList)
admin.site.register(Line)
