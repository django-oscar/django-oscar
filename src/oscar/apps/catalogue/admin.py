from django.contrib import admin
from server.apps.catalogue.models import ProductBranch
from server.apps.partner.models import StockRecord
from server.apps.service.models import Service, ServicePolicy
from treebeard.admin import TreeAdmin
from treebeard.forms import movenodeform_factory, MoveNodeForm
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
# ServicePolicy = get_model("Service", "ServicePolicy")


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
        "max_notice_days",
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

class ServicePolicyInline(admin.StackedInline):
    model = ServicePolicy
    extra = 0
    max_num = 1


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

class CategoryMoveForm(MoveNodeForm):
    """
    A custom form that allows creating root nodes if the user
    doesn't pick a parent node (i.e. _ref_node_id is empty).
    """
    def save(self, commit=True):
        # If user selected no parent (i.e. _ref_node_id not supplied),
        # we'll create a root node via add_root() instead of the usual move logic.
        if not self.cleaned_data.get('_ref_node_id'):
            # Make a new root. We copy relevant fields from self.cleaned_data
            # onto a brand new instance:
            model_cls = self.instance.__class__
            root_instance = model_cls.add_root(
                name=self.cleaned_data.get('name'),
                slug=self.cleaned_data.get('slug'),
                vendor=self.cleaned_data.get('vendor'),
                description=self.cleaned_data.get('description'),
                # ... copy any other fields as needed ...
            )
            # If you have translations or custom logic, add them here:
            root_instance.name_en = self.cleaned_data.get('name_en', '')
            root_instance.name_ar = self.cleaned_data.get('name_ar', '')
            root_instance.description_en = self.cleaned_data.get('description_en', '')
            root_instance.description_ar = self.cleaned_data.get('description_ar', '')
            # And so on.

            if commit:
                root_instance.save()

            # Return the new node instance
            return root_instance

        # Otherwise, fallback to normal move logic (child node under an existing parent)
        return super().save(commit=commit)
    
class CategoryAdmin(TreeAdmin):
    form = CategoryMoveForm
    list_display = (
        "name", "vendor", "is_public", "order", "meta_title", "depth", "numchild"
    )
    list_filter = ("vendor", "is_public")
    search_fields = ("name", "vendor__name", "meta_title")
    ordering = ("vendor", "order")
    list_editable = ("is_public", "order")

    # Add them to readonly_fields so Django won't treat them as form fields
    readonly_fields = ("depth", "path", "numchild")
    
    fieldsets = (
        (None, {
            "fields": (
                "name", "name_en", "name_ar", 
                "slug", "vendor",
                "description", "description_en", "description_ar", 
                "image",
                "_position", "_ref_node_id"
            )
        }),
        ("Visibility", {
            "fields": ("is_public", "order")
        }),
        ("SEO", {
            "fields": ("meta_title", "meta_description")
        }),
        ("Tree Structure", {
            "fields": ("depth", "path", "numchild"),  # read-only now
            "description": "Automatically managed fields for category hierarchy."
        }),
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
