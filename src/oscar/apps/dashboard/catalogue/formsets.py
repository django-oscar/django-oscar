from django import forms
from django.core import exceptions
from django.forms.models import inlineformset_factory
from django.utils.translation import gettext_lazy as _

from oscar.core.loading import get_classes, get_model
from server.apps.catalogue.models import Category, ProductBranch
from server.apps.dashboard.catalogue.forms import ProductBranchForm
from server.apps.vendor.models import Vendor
from stores.models import Store


Product = get_model("catalogue", "Product")
ProductClass = get_model("catalogue", "ProductClass")
ProductAttribute = get_model("catalogue", "ProductAttribute")
StockRecord = get_model("partner", "StockRecord")
ProductCategory = get_model("catalogue", "ProductCategory")
ProductImage = get_model("catalogue", "ProductImage")
ProductRecommendation = get_model("catalogue", "ProductRecommendation")
AttributeOptionGroup = get_model("catalogue", "AttributeOptionGroup")
AttributeOption = get_model("catalogue", "AttributeOption")
Option = get_model('catalogue', 'Option')
Store = get_model("stores", "Store")

(
    StockRecordForm,
    ProductCategoryForm,
    ProductImageForm,
    ProductRecommendationForm,
    ProductAttributesForm,
    AttributeOptionForm,
) = get_classes(
    "dashboard.catalogue.forms",
    (
        "StockRecordForm",
        "ProductCategoryForm",
        "ProductImageForm",
        "ProductRecommendationForm",
        "ProductAttributesForm",
        "AttributeOptionForm",
    ),
)


BaseStockRecordFormSet = inlineformset_factory(
    Product, StockRecord, form=StockRecordForm, extra=10
)


class StockRecordFormSet(BaseStockRecordFormSet):
    def __init__(self, product_class, user, *args, **kwargs):
        self.user = user
        self.require_user_stockrecord = not (
            user.is_staff or Vendor.objects.filter(user=user).exists()
        )
        self.product_class = product_class

        if not user.is_staff and "instance" in kwargs and "queryset" not in kwargs:
            kwargs.update(
                {
                    "queryset": StockRecord.objects.filter(
                        product=kwargs["instance"], partner__in=user.partners.all()
                    )
                }
            )

        super().__init__(*args, **kwargs)
        self.set_initial_data()

    def set_initial_data(self):
        """
        If user has only one partner associated, set the first
        stock record's partner to it. Can't pre-select for staff users as
        they're allowed to save a product without a stock record.

        This is intentionally done after calling __init__ as passing initial
        data to __init__ creates a form for each list item. So depending on
        whether we can pre-select the partner or not, we'd end up with 1 or 2
        forms for an unbound form.
        """
        if self.require_user_stockrecord:
            try:
                user_partner = self.user.partners.get()
            except (exceptions.ObjectDoesNotExist, exceptions.MultipleObjectsReturned):
                pass
            else:
                partner_field = self.forms[0].fields.get("partner", None)
                if partner_field and partner_field.initial is None:
                    partner_field.initial = user_partner

    def _construct_form(self, i, **kwargs):
        kwargs["product_class"] = self.product_class
        kwargs["user"] = self.user
        return super()._construct_form(i, **kwargs)

    def clean(self):
        """
        If the user isn't a staff user, this validation ensures that at least
        one stock record's partner is associated with a users partners.
        """
        if any(self.errors):
            return
        if self.require_user_stockrecord:
            stockrecord_partners = set(
                [form.cleaned_data.get("partner", None) for form in self.forms]
            )
            user_partners = set(self.user.partners.all())
            if not user_partners & stockrecord_partners:
                raise exceptions.ValidationError(
                    _(
                        "At least one stock record must be set to a partner that"
                        " you're associated with."
                    )
                )


BaseProductCategoryFormSet = inlineformset_factory(
    Product, ProductCategory, form=ProductCategoryForm, extra=10, can_delete=True
)


class ProductCategoryFormSet(BaseProductCategoryFormSet):
    def __init__(self, product_class, user, *args, **kwargs):
        super().__init__(*args, **kwargs)  # Ensure the formset is fully initialized first

        # Check if the user has an associated vendor
        self.vendor = Vendor.objects.filter(user=user).first()
        if not self.vendor:
            raise ValueError("The user does not have an associated vendor.")

        # Apply vendor-related queryset filtering only after initializing the formset
        for form in self.forms:
            form.fields['category'].queryset = Category.objects.filter(vendor=self.vendor)

        # Add category details for debugging (optional)
        for form in self.forms:
            if 'category' in form.fields:
                categories = form.fields['category'].queryset
                # for category in categories:
                    # print(f"Category Name: {category.name}, Description: {category.description}")


    def clean(self):
        if not self.instance.is_child and self.get_num_categories() == 0:
            raise forms.ValidationError(
                _("products must have at least one category")
            )
        if self.instance.is_child and self.get_num_categories() > 0:
            raise forms.ValidationError(_("A child product should not have categories"))

    def get_num_categories(self):
        num_categories = 0
        for i in range(0, self.total_form_count()):
            form = self.forms[i]
            if (
                hasattr(form, "cleaned_data")
                and form.cleaned_data.get("category", None)
                and not form.cleaned_data.get("DELETE", False)
            ):
                num_categories += 1
        return num_categories


BaseProductImageFormSet = inlineformset_factory(
    Product, ProductImage, form=ProductImageForm, extra=5
)


class ProductImageFormSet(BaseProductImageFormSet):
    # pylint: disable=unused-argument
    def __init__(self, product_class, user, *args, **kwargs):
        super().__init__(*args, **kwargs)


BaseProductRecommendationFormSet = inlineformset_factory(
    Product,
    ProductRecommendation,
    form=ProductRecommendationForm,
    extra=5,
    fk_name="primary",
)


class ProductRecommendationFormSet(BaseProductRecommendationFormSet):
    def __init__(self, product_class, user, *args, **kwargs):
        # Retrieve the vendor associated with the user
        self.user = user
        self.vendor = Vendor.objects.filter(user=user).first()
        if not self.vendor:
            raise ValueError("The user does not have an associated vendor.")
        
        # Initialize the formset after setting vendor
        super().__init__(*args, **kwargs)
        
        # Initially set an empty queryset for the recommendation field
        for form in self.forms:
            form.fields["recommendation"].queryset = Product.objects.none()
            # Debug: print to confirm the initial empty state
            # print("Initial empty recommendation queryset:", form.fields["recommendation"].queryset)

        # Fetch vendor-specific products and apply to recommendation fields if available
        vendor_products = Product.objects.filter(vendor=self.vendor)
        if vendor_products.exists():
            for form in self.forms:
                form.fields["recommendation"].queryset = vendor_products
                # Debug: print to confirm vendor-specific queryset is applied
                # print("Vendor-specific recommendation queryset:", form.fields["recommendation"].queryset)

ProductAttributesFormSet = inlineformset_factory(
    ProductClass, ProductAttribute, form=ProductAttributesForm, extra=3
)


AttributeOptionFormSet = inlineformset_factory(
    AttributeOptionGroup, AttributeOption, form=AttributeOptionForm, extra=3
)


BaseProductBranchFormSet = inlineformset_factory(
    # The parent model
    parent_model=Product,
    # The model that points to Product via a ForeignKey
    model=ProductBranch,
    form=ProductBranchForm,
    extra=1,            # Number of empty forms to display
    can_delete=True,    # Allow deleting existing relations
)



class ProductBranchFormSet(BaseProductBranchFormSet):
    """
    Inline formset for linking Products to Branches (Stores).
    """
    def __init__(self, product_class, user, *args, **kwargs):
        """
        product_class and user are passed in so we can do
        filtering on the user's vendor, similar to how StockRecordFormSet 
        or ProductCategoryFormSet are initialized.
        """
        super().__init__(*args, **kwargs)

        # Get the vendor associated with the user
        self.vendor = Vendor.objects.filter(user=user).first()
        if not self.vendor:
            raise ValueError("The user does not have an associated vendor.")

        # Restrict branch queryset to only those belonging to the vendor
        for form in self.forms:
            if "branch" in form.fields:
                form.fields["branch"].queryset = Store.objects.filter(vendor=self.vendor)

    def clean(self):
        """
        Optionally enforce any additional business logic:
          - For example, if the product is a child product,
            you might disallow any branches.
        """
        super().clean()

        num_branches = 0
        for form in self.forms:
            if (
                hasattr(form, 'cleaned_data')
                and form.cleaned_data.get('branch') is not None
                and not form.cleaned_data.get('DELETE', False)
            ):
                num_branches += 1

        # if self.instance.is_child:
        #     # Child products should not have branches
        #     if num_branches > 0:
        #         raise forms.ValidationError(
        #             _("A child product should not have branches assigned.")
        #         )
        # else:
        #     # Parent products must have at least one branch
        #     if num_branches == 0:
        #         raise forms.ValidationError(
        #             _("Products must have at least one branch assigned.")
        #         )


# Inline formset for the M2M "through" relationship between Product and Option.
BaseProductOptionFormSet = inlineformset_factory(
    parent_model=Product,
    model=Product.product_options.through,  # the implicit "through" table behind product->option
    fields=['option'],
    extra=2,
    can_delete=True
)


class ProductOptionFormSet(BaseProductOptionFormSet):
    """
    Manage Product->Option many-to-many relationships in the dashboard.
    If you want to restrict which Options are visible, you can tweak 
    the queryset in __init__.
    """
    def __init__(self, product_class, user, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Example: if you only want to show Options that belong to 
        # some vendor or some condition, filter here:
        #
        # for form in self.forms:
        #     if 'option' in form.fields:
        #         form.fields['option'].queryset = Option.objects.filter(...)