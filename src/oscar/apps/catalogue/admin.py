from django.contrib import admin
from server.apps.catalogue.models import ProductBranch
from server.apps.partner.models import StockRecord
from server.apps.service.models import Service
from treebeard.admin import TreeAdmin
from treebeard.forms import movenodeform_factory
from django.utils.safestring import mark_safe

from oscar.core.loading import get_model

AttributeOption = get_model("catalogue", "AttributeOption")
AttributeOptionGroup = get_model("catalogue", "AttributeOptionGroup")
Category = get_model("catalogue", "Category")
Option = get_model("catalogue", "Option")
Product = get_model("catalogue", "Product")
ProductAttribute = get_model("catalogue", "ProductAttribute")
ProductAttributeValue = get_model("catalogue", "ProductAttributeValue")
ProductCategory = get_model("catalogue", "ProductCategory")
ProductClass = get_model("catalogue", "ProductClass")
ProductImage = get_model("catalogue", "ProductImage")
ProductRecommendation = get_model("catalogue", "ProductRecommendation")


class AttributeInline(admin.TabularInline):
    model = ProductAttributeValue


class ProductRecommendationInline(admin.TabularInline):
    model = ProductRecommendation
    fk_name = "primary"
    raw_id_fields = ["primary", "recommendation"]


class CategoryInline(admin.TabularInline):
    model = ProductCategory
    extra = 1


class ProductAttributeInline(admin.TabularInline):
    model = ProductAttribute
    extra = 2


class ProductClassAdmin(admin.ModelAdmin):
    list_display = ("name", "track_stock")
    inlines = [ProductAttributeInline]

class ProductBranchInline(admin.TabularInline):
    model = ProductBranch
    extra = 1
    verbose_name = "Branch"
    verbose_name_plural = "Branches"

class ProductStockInline(admin.TabularInline):
    model = StockRecord
    extra = 1
    verbose_name = "Stock Record"
    verbose_name_plural = "Stock Records"

class ProductServiceInline(admin.TabularInline):
    model = Service
    extra = 1
    verbose_name = "Service"
    verbose_name_plural = "Services"
    readonly_fields = ("get_dynamic_time_slots",)
    fields = (
        "branch",
        "service_type",
        "provider_name",
        "duration_minutes",
        "max_services_per_slot",
        "max_future_days",
        "get_dynamic_time_slots",
    )

    def get_dynamic_time_slots(self, obj):
        """
        Display available time slots for each service in a table format.
        """
        if not obj or not obj.pk:  # Handle unsaved or empty objects
            return "Save the service to see available time slots."

        slots_data = obj.get_available_time_slots()
        if not slots_data:
            return "No available time slots."

        # Build an HTML table for displaying slots
        html_output = '<table style="border-collapse: collapse; width: 100%; border: 1px solid #ddd;">'
        html_output += '<thead><tr><th style="border: 1px solid #ddd; padding: 8px;">Date</th>'
        html_output += '<th style="border: 1px solid #ddd; padding: 8px;">Weekday</th>'
        html_output += '<th style="border: 1px solid #ddd; padding: 8px;">Time Slots</th></tr></thead>'
        html_output += '<tbody>'

        for day_data in slots_data:
            date = day_data.get("date", "N/A")
            weekday = day_data.get("weekday", "N/A")
            slots = day_data.get("slots", [])

            slots_str = ", ".join([f"{slot['start']} - {slot['end']}" for slot in slots])
            html_output += f'<tr><td style="border: 1px solid #ddd; padding: 8px;">{date}</td>'
            html_output += f'<td style="border: 1px solid #ddd; padding: 8px;">{weekday}</td>'
            html_output += f'<td style="border: 1px solid #ddd; padding: 8px;">{slots_str}</td></tr>'

        html_output += '</tbody></table>'
        return mark_safe(html_output)

    get_dynamic_time_slots.short_description = "Dynamic Time Slots"



class ProductAdmin(admin.ModelAdmin):
    date_hierarchy = "date_created"
    list_display = (
        "get_title",
        "upc",
        "get_product_class",
        # "structure",
        "attribute_summary",
        "date_created",
    )
    # list_filter = [ "is_discountable"]
    raw_id_fields = ["parent"]
    inlines = [AttributeInline, CategoryInline, ProductRecommendationInline, ProductBranchInline, ProductStockInline, ProductServiceInline]
    prepopulated_fields = {"slug": ("title",)}
    search_fields = ["upc", "title"]

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related("product_class", "parent").prefetch_related(
            "attribute_values", "attribute_values__attribute"
        )


class ProductAttributeAdmin(admin.ModelAdmin):
    list_display = ("name", "code", "product_class", "type")
    prepopulated_fields = {"code": ("name",)}


class OptionAdmin(admin.ModelAdmin):
    pass


class ProductAttributeValueAdmin(admin.ModelAdmin):
    list_display = ("product", "attribute", "value")


class AttributeOptionInline(admin.TabularInline):
    model = AttributeOption


class AttributeOptionGroupAdmin(admin.ModelAdmin):
    list_display = ("name", "option_summary")
    inlines = [
        AttributeOptionInline,
    ]


class CategoryAdmin(TreeAdmin):
    # Use the form for handling tree structure
    form = movenodeform_factory(Category)
    
    # Add fields to the list display
    list_display = ("name", "vendor", "slug", "is_public", "order", "meta_title")
    
    # Add filters for the admin panel
    list_filter = ("vendor", "is_public")
    
    # Add search capabilities
    search_fields = ("name", "slug", "vendor__name", "meta_title")
    
    # Add ordering for the admin panel
    ordering = ("vendor", "order")
    
    # Enable editing fields directly in the list view
    list_editable = ("is_public", "order")
    
    # Customize fieldsets (Optional)
    fieldsets = (
        (None, {"fields": ("name_en", "name_ar", "slug", "vendor", "description", "description_en", "description_ar", "image")}),
        ("Visibility", {"fields": ("is_public", "order")}),
        ("SEO", {"fields": ("meta_title", "meta_description")}),
    )


admin.site.register(ProductClass, ProductClassAdmin)
admin.site.register(Product, ProductAdmin)
admin.site.register(ProductAttribute, ProductAttributeAdmin)
admin.site.register(ProductAttributeValue, ProductAttributeValueAdmin)
admin.site.register(AttributeOptionGroup, AttributeOptionGroupAdmin)
admin.site.register(Option, OptionAdmin)
admin.site.register(ProductImage)
admin.site.register(Category, CategoryAdmin)
admin.site.register(ProductCategory)
