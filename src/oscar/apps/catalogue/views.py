from urllib.parse import quote

from django.http import Http404, HttpResponsePermanentRedirect
from django.utils.translation import gettext_lazy as _
from django.views.generic import DetailView

from oscar.apps.catalogue.signals import product_viewed
from oscar.core.loading import get_class, get_model

Product = get_model("catalogue", "product")
Category = get_model("catalogue", "category")
ProductAlert = get_model("customer", "ProductAlert")
ProductAlertForm = get_class("customer.forms", "ProductAlertForm")


class ProductDetailView(DetailView):
    context_object_name = "product"
    model = Product
    view_signal = product_viewed
    template_folder = "catalogue"

    # Whether to redirect to the URL with the right path
    enforce_paths = True

    # Whether to redirect child products to their parent's URL. If it's disabled,
    # we display variant product details on the separate page. Otherwise, details
    # displayed on parent product page.
    enforce_parent = False

    def get(self, request, *args, **kwargs):
        """
        Ensures that the correct URL is used before rendering a response
        """
        # pylint: disable=attribute-defined-outside-init
        self.object = product = self.get_object()

        if redirect_to := self.redirect_if_necessary(request.path, product):
            return redirect_to

        # Do allow staff members so they can test layout etc.
        if not self.is_viewable(product, request):
            raise Http404()

        response = super().get(request, *args, **kwargs)
        self.send_signal(request, response, product)
        return response

    def is_viewable(self, product, request):
        if product.is_child:
            return (
                product.is_public and product.parent.is_public
            ) or request.user.is_staff

        return product.is_public or request.user.is_staff

    def get_object(self, queryset=None):
        # Check if self.object is already set to prevent unnecessary DB calls
        if hasattr(self, "object"):
            return self.object
        else:
            return super().get_object(queryset)

    def redirect_if_necessary(self, current_path, product):
        if self.enforce_parent and product.is_child:
            return HttpResponsePermanentRedirect(product.parent.get_absolute_url())

        if self.enforce_paths:
            expected_path = product.get_absolute_url()
            if quote(expected_path) != quote(current_path):
                return HttpResponsePermanentRedirect(expected_path)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["alert_form"] = self.get_alert_form()
        ctx["has_active_alert"] = self.get_alert_status()
        return ctx

    def get_alert_status(self):
        # Check if this user already have an alert for this product
        has_alert = False
        if self.request.user.is_authenticated:
            alerts = ProductAlert.objects.filter(
                product=self.object, user=self.request.user, status=ProductAlert.ACTIVE
            )
            has_alert = alerts.exists()
        return has_alert

    def get_alert_form(self):
        return ProductAlertForm(user=self.request.user, product=self.object)

    def send_signal(self, request, response, product):
        self.view_signal.send(
            sender=self,
            product=product,
            user=request.user,
            request=request,
            response=response,
        )

    def get_template_names(self):
        """
        Return a list of possible templates.

        If an overriding class sets a template name, we use that. Otherwise,
        we try 2 options before defaulting to :file:`catalogue/detail.html`:

            1. :file:`detail-for-upc-{upc}.html`
            2. :file:`detail-for-class-{classname}.html`

        This allows alternative templates to be provided for a per-product
        and a per-item-class basis.
        """
        if self.template_name:
            return [self.template_name]

        return [
            "oscar/%s/detail-for-upc-%s.html" % (self.template_folder, self.object.upc),
            "oscar/%s/detail-for-class-%s.html"
            % (self.template_folder, self.object.get_product_class().slug),
            "oscar/%s/detail.html" % self.template_folder,
        ]


# Import catalogue and category view from search app
CatalogueView = get_class("search.views", "CatalogueView")
ProductCategoryView = get_class("search.views", "ProductCategoryView")
