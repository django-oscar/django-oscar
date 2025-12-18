from django.contrib import admin

from oscar.core.loading import get_model

ProductAlert = get_model("customer", "ProductAlert")


class ProductAlertAdmin(admin.ModelAdmin):
    list_display = ("product", "user", "status", "date_created")
    search_fields = ("product__title", "product__upc", "user__username", "user__email")
    autocomplete_fields = ("user", "product")
    list_filter = ("status",)


admin.site.register(ProductAlert, ProductAlertAdmin)
