from django.conf import settings
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _
from django.utils.translation import ngettext_lazy
from django_tables2 import A, Column, LinkColumn, TemplateColumn

from oscar.core.loading import get_class, get_model

DashboardTable = get_class("dashboard.tables", "DashboardTable")
Product = get_model("catalogue", "Product")
Category = get_model("catalogue", "Category")
AttributeOptionGroup = get_model("catalogue", "AttributeOptionGroup")
Option = get_model("catalogue", "Option")


class ProductTable(DashboardTable):
    title = TemplateColumn(
        verbose_name=_("Title"),
        template_name="oscar/dashboard/catalogue/product_row_title.html",
        order_by="title",
        accessor=A("title"),
    )
    image = TemplateColumn(
        verbose_name=_("Image"),
        template_name="oscar/dashboard/catalogue/product_row_image.html",
        orderable=False,
    )
    product_class = Column(
        verbose_name=_("Product type"),
        accessor=A("product_class"),
        order_by="product_class__name",
    )
    variants = TemplateColumn(
        verbose_name=_("Variants"),
        template_name="oscar/dashboard/catalogue/product_row_variants.html",
        orderable=False,
    )
    stock_records = TemplateColumn(
        verbose_name=_("Stock records"),
        template_name="oscar/dashboard/catalogue/product_row_stockrecords.html",
        orderable=False,
    )
    actions = TemplateColumn(
        verbose_name=_("Actions"),
        template_name="oscar/dashboard/catalogue/product_row_actions.html",
        orderable=False,
    )

    is_public = TemplateColumn(
        template_code='''
        <input type="checkbox"
               data-id="{{ record.id }}"
               class="product-is-public-toggle is-public-toggle"
               {% if record.is_public %}checked{% endif %}>
        ''',
        verbose_name=_("Is Public"),
        orderable=True,
    )
    
    icon = "fas fa-sitemap"

    class Meta(DashboardTable.Meta):
        model = Product
        fields = ("upc", "is_public", "date_updated")
        sequence = (
            "title",
            "upc",
            "image",
            "product_class",
            "variants",
            "stock_records",
            "...",
            "is_public",
            "date_updated",
            "actions",
        )
        order_by = "-date_updated"


class CategoryTable(DashboardTable):
    caption_text = _("Categories")  # Set the caption text
    icon_svg = '''<svg width="20" height="20" viewBox="0 0 20 20" fill="none" xmlns="http://www.w3.org/2000/svg">
<path d="M4.99984 3.33329C4.99984 4.25377 4.25365 4.99996 3.33317 4.99996C2.4127 4.99996 1.6665 4.25377 1.6665 3.33329C1.6665 2.41282 2.4127 1.66663 3.33317 1.66663C4.25365 1.66663 4.99984 2.41282 4.99984 3.33329Z" stroke="#FF2E00" stroke-width="1.25" stroke-linecap="round" stroke-linejoin="round"/>
<path d="M4.99984 9.99996C4.99984 10.9204 4.25365 11.6666 3.33317 11.6666C2.4127 11.6666 1.6665 10.9204 1.6665 9.99996C1.6665 9.07948 2.4127 8.33329 3.33317 8.33329C4.25365 8.33329 4.99984 9.07948 4.99984 9.99996Z" stroke="#FF2E00" stroke-width="1.25" stroke-linecap="round" stroke-linejoin="round"/>
<path d="M4.99984 16.6666C4.99984 17.5871 4.25365 18.3333 3.33317 18.3333C2.4127 18.3333 1.6665 17.5871 1.6665 16.6666C1.6665 15.7462 2.4127 15 3.33317 15C4.25365 15 4.99984 15.7462 4.99984 16.6666Z" stroke="#FF2E00" stroke-width="1.25" stroke-linecap="round" stroke-linejoin="round"/>
<path d="M11.6665 3.33329C11.6665 4.25377 10.9203 4.99996 9.99984 4.99996C9.07936 4.99996 8.33317 4.25377 8.33317 3.33329C8.33317 2.41282 9.07936 1.66663 9.99984 1.66663C10.9203 1.66663 11.6665 2.41282 11.6665 3.33329Z" stroke="#FF2E00" stroke-width="1.25" stroke-linecap="round" stroke-linejoin="round"/>
<path d="M11.6665 9.99996C11.6665 10.9204 10.9203 11.6666 9.99984 11.6666C9.07936 11.6666 8.33317 10.9204 8.33317 9.99996C8.33317 9.07948 9.07936 8.33329 9.99984 8.33329C10.9203 8.33329 11.6665 9.07948 11.6665 9.99996Z" stroke="#FF2E00" stroke-width="1.25" stroke-linecap="round" stroke-linejoin="round"/>
<path d="M11.6665 16.6666C11.6665 17.5871 10.9203 18.3333 9.99984 18.3333C9.07936 18.3333 8.33317 17.5871 8.33317 16.6666C8.33317 15.7462 9.07936 15 9.99984 15C10.9203 15 11.6665 15.7462 11.6665 16.6666Z" stroke="#FF2E00" stroke-width="1.25" stroke-linecap="round" stroke-linejoin="round"/>
<path d="M18.3332 3.33329C18.3332 4.25377 17.587 4.99996 16.6665 4.99996C15.746 4.99996 14.9998 4.25377 14.9998 3.33329C14.9998 2.41282 15.746 1.66663 16.6665 1.66663C17.587 1.66663 18.3332 2.41282 18.3332 3.33329Z" stroke="#FF2E00" stroke-width="1.25" stroke-linecap="round" stroke-linejoin="round"/>
<path d="M18.3332 9.99996C18.3332 10.9204 17.587 11.6666 16.6665 11.6666C15.746 11.6666 14.9998 10.9204 14.9998 9.99996C14.9998 9.07948 15.746 8.33329 16.6665 8.33329C17.587 8.33329 18.3332 9.07948 18.3332 9.99996Z" stroke="#FF2E00" stroke-width="1.25" stroke-linecap="round" stroke-linejoin="round"/>
<path d="M18.3332 16.6666C18.3332 17.5871 17.587 18.3333 16.6665 18.3333C15.746 18.3333 14.9998 17.5871 14.9998 16.6666C14.9998 15.7462 15.746 15 16.6665 15C17.587 15 18.3332 15.7462 18.3332 16.6666Z" stroke="#FF2E00" stroke-width="1.25" stroke-linecap="round" stroke-linejoin="round"/>
</svg>
'''
    name = LinkColumn("dashboard:catalogue-category-update", args=[A("pk")])
    description = TemplateColumn(
        template_code='{{ record.description|default:""|striptags'
        '|cut:"&nbsp;"|truncatewords:6 }}'
    )
    # mark_safe is needed because of
    # https://github.com/bradleyayers/django-tables2/issues/187
    num_children = LinkColumn(
        "dashboard:catalogue-category-detail-list",
        args=[A("pk")],
        verbose_name=mark_safe(_("Number of child categories")),
        accessor="get_num_children",
        orderable=False,
    )
    actions = TemplateColumn(
        template_name="oscar/dashboard/catalogue/category_row_actions.html",
        orderable=False,
    )
    is_public = TemplateColumn(
        template_code='''
        <input type="checkbox" data-id="{{ record.id }}" class="is-public-toggle" {% if record.is_public %}checked{% endif %}>
        ''',
        verbose_name=_("Is Public"),
        orderable=True,
    )
    order = TemplateColumn(
        template_code='''{{ record.order }}''',
        verbose_name=_("Order"),
        orderable=True,  # Enable ordering by this column
    )

    icon = "sitemap"
    caption = ngettext_lazy("%s Category", "%s Categories")

    class Meta(DashboardTable.Meta):
        model = Category
        fields = ("name", "description", "is_public", "order")
        sequence = ("name", "description", "...", "is_public", "order", "actions")


class AttributeOptionGroupTable(DashboardTable):
    name = TemplateColumn(
        verbose_name=_("Name"),
        template_name="oscar/dashboard/catalogue/attribute_option_group_row_name.html",
        order_by="name",
    )
    option_summary = TemplateColumn(
        verbose_name=_("Option summary"),
        template_name="oscar/dashboard/catalogue/attribute_option_group_row_option_summary.html",
        orderable=False,
    )
    actions = TemplateColumn(
        verbose_name=_("Actions"),
        template_name="oscar/dashboard/catalogue/attribute_option_group_row_actions.html",
        orderable=False,
    )

    icon = "sitemap"
    caption = ngettext_lazy("%s Attribute Option Group", "%s Attribute Option Groups")

    class Meta(DashboardTable.Meta):
        model = AttributeOptionGroup
        fields = ("name",)
        sequence = ("name", "option_summary", "actions")
        per_page = settings.OSCAR_DASHBOARD_ITEMS_PER_PAGE


class OptionTable(DashboardTable):
    name = TemplateColumn(
        verbose_name=_("Name"),
        template_name="oscar/dashboard/catalogue/option_row_name.html",
        order_by="name",
    )
    actions = TemplateColumn(
        verbose_name=_("Actions"),
        template_name="oscar/dashboard/catalogue/option_row_actions.html",
        orderable=False,
    )

    icon = "reorder"
    caption = ngettext_lazy("%s Option", "%s Options")

    class Meta(DashboardTable.Meta):
        model = Option
        fields = ("name", "type", "required")
        sequence = ("name", "type", "required", "actions")
        per_page = settings.OSCAR_DASHBOARD_ITEMS_PER_PAGE
