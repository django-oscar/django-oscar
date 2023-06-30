# pylint: disable=attribute-defined-outside-init
import csv

from django.conf import settings
from django.contrib import messages
from django.db import transaction
from django.db.models import Count
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.views import generic

from oscar.core.loading import get_class, get_model
from oscar.core.utils import slugify
from oscar.views import sort_queryset

VoucherForm = get_class("dashboard.vouchers.forms", "VoucherForm")
VoucherSetForm = get_class("dashboard.vouchers.forms", "VoucherSetForm")
VoucherSetSearchForm = get_class("dashboard.vouchers.forms", "VoucherSetSearchForm")
VoucherSearchForm = get_class("dashboard.vouchers.forms", "VoucherSearchForm")
Voucher = get_model("voucher", "Voucher")
VoucherSet = get_model("voucher", "VoucherSet")
OrderDiscount = get_model("order", "OrderDiscount")


class VoucherListView(generic.ListView):
    model = Voucher
    context_object_name = "vouchers"
    template_name = "oscar/dashboard/vouchers/voucher_list.html"
    form_class = VoucherSearchForm
    paginate_by = settings.OSCAR_DASHBOARD_ITEMS_PER_PAGE

    def get_queryset(self):
        self.search_filters = []
        qs = self.model._default_manager.all()
        qs = qs.annotate(num_offers=Count("offers", distinct=True))
        qs = sort_queryset(
            qs,
            self.request,
            ["num_basket_additions", "num_orders", "num_offers", "date_created"],
            "-date_created",
        )

        # If form is not submitted, perform a default filter, and return early
        if not self.request.GET:
            self.form = self.form_class(initial={"in_set": False})
            # This form is exactly the same as the other one, apart from having
            # fields with different IDs, so that they are unique within the page
            # (non-unique field IDs also break Select2)
            self.advanced_form = self.form_class(
                initial={"in_set": False}, auto_id="id_advanced_%s"
            )
            self.search_filters.append(_("Not in a set"))
            return qs.filter(voucher_set__isnull=True)

        self.form = self.form_class(self.request.GET)
        # This form is exactly the same as the other one, apart from having
        # fields with different IDs, so that they are unique within the page
        # (non-unique field IDs also break Select2)
        self.advanced_form = self.form_class(self.request.GET, auto_id="id_advanced_%s")
        if not all([self.form.is_valid(), self.advanced_form.is_valid()]):
            return qs

        name = self.form.cleaned_data["name"]
        code = self.form.cleaned_data["code"]
        offer_name = self.form.cleaned_data["offer_name"]
        is_active = self.form.cleaned_data["is_active"]
        in_set = self.form.cleaned_data["in_set"]
        has_offers = self.form.cleaned_data["has_offers"]

        if name:
            qs = qs.filter(name__icontains=name)
            self.search_filters.append(_('Name matches "%s"') % name)
        if code:
            qs = qs.filter(code=code)
            self.search_filters.append(_('Code is "%s"') % code)
        if offer_name:
            qs = qs.filter(offers__name__icontains=offer_name)
            self.search_filters.append(_('Offer name matches "%s"') % offer_name)
        if is_active is not None:
            now = timezone.now()
            if is_active:
                qs = qs.filter(start_datetime__lte=now, end_datetime__gte=now)
                self.search_filters.append(_("Is active"))
            else:
                qs = qs.filter(end_datetime__lt=now)
                self.search_filters.append(_("Is inactive"))
        if in_set is not None:
            qs = qs.filter(voucher_set__isnull=not in_set)
            self.search_filters.append(_("In a set") if in_set else _("Not in a set"))
        if has_offers is not None:
            qs = qs.filter(offers__isnull=not has_offers).distinct()
            self.search_filters.append(
                _("Has offers") if has_offers else _("Has no offers")
            )

        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["form"] = self.form
        ctx["advanced_form"] = self.advanced_form
        ctx["search_filters"] = self.search_filters
        return ctx


class VoucherCreateView(generic.CreateView):
    model = Voucher
    template_name = "oscar/dashboard/vouchers/voucher_form.html"
    form_class = VoucherForm
    success_url = reverse_lazy("dashboard:voucher-list")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["title"] = _("Create voucher")
        return ctx

    def get_initial(self):
        initial = super().get_initial()
        initial["start_datetime"] = timezone.now()
        return initial

    @transaction.atomic()
    def form_valid(self, form):
        response = super().form_valid(form)
        self.object.offers.add(*form.cleaned_data["offers"])
        return response

    def get_success_url(self):
        messages.success(self.request, _("Voucher created"))
        return super().get_success_url()


class VoucherStatsView(generic.DetailView):
    model = Voucher
    template_name = "oscar/dashboard/vouchers/voucher_detail.html"
    context_object_name = "voucher"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        discounts = OrderDiscount.objects.filter(voucher_id=self.object.id)
        discounts = discounts.order_by("-order__date_placed")
        ctx["discounts"] = discounts
        return ctx


class VoucherUpdateView(generic.UpdateView):
    template_name = "oscar/dashboard/vouchers/voucher_form.html"
    context_object_name = "voucher"
    model = Voucher
    form_class = VoucherForm
    success_url = reverse_lazy("dashboard:voucher-list")

    def dispatch(self, request, *args, **kwargs):
        voucher_set = self.get_object().voucher_set
        if voucher_set is not None:
            messages.warning(
                request, _("The voucher can only be edited as part of its set")
            )
            return redirect("dashboard:voucher-set-update", pk=voucher_set.pk)
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["title"] = self.object.name
        return ctx

    def get_initial(self):
        initial = super().get_initial()
        initial["offers"] = self.object.offers.all()
        return initial

    @transaction.atomic()
    def form_valid(self, form):
        response = super().form_valid(form)
        self.object.offers.set(form.cleaned_data["offers"])
        return response

    def get_success_url(self):
        messages.success(self.request, _("Voucher updated"))
        return super().get_success_url()


class VoucherDeleteView(generic.DeleteView):
    model = Voucher
    template_name = "oscar/dashboard/vouchers/voucher_delete.html"
    context_object_name = "voucher"

    @transaction.atomic
    def delete(self, request, *args, **kwargs):
        response = super().delete(request, *args, **kwargs)
        if self.object.voucher_set is not None:
            self.object.voucher_set.update_count()
        return response

    def post(self, request, *args, **kwargs):
        return self.delete(request, *args, **kwargs)

    def get_success_url(self):
        messages.warning(self.request, _("Voucher deleted"))
        if self.object.voucher_set is not None:
            return reverse(
                "dashboard:voucher-set-detail",
                kwargs={"pk": self.object.voucher_set.pk},
            )
        else:
            return reverse("dashboard:voucher-list")


class VoucherSetCreateView(generic.CreateView):
    model = VoucherSet
    template_name = "oscar/dashboard/vouchers/voucher_set_form.html"
    form_class = VoucherSetForm

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["title"] = _("Create voucher set")
        return ctx

    def get_initial(self):
        initial = super().get_initial()
        initial["start_datetime"] = timezone.now()
        return initial

    def get_success_url(self):
        messages.success(self.request, _("Voucher set created"))
        return reverse("dashboard:voucher-set-list")


class VoucherSetUpdateView(generic.UpdateView):
    template_name = "oscar/dashboard/vouchers/voucher_set_form.html"
    model = VoucherSet
    context_object_name = "voucher_set"
    form_class = VoucherSetForm

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["title"] = self.object.name
        return ctx

    def get_initial(self):
        initial = super().get_initial()
        # All vouchers in the set have the same "usage" and "offers", so we use
        # the first one
        voucher = self.object.vouchers.first()
        if voucher is not None:
            initial["usage"] = voucher.usage
            initial["offers"] = voucher.offers.all()
        return initial

    def get_success_url(self):
        messages.success(self.request, _("Voucher updated"))
        return reverse("dashboard:voucher-set-detail", kwargs={"pk": self.object.pk})


class VoucherSetDetailView(generic.ListView):
    model = Voucher
    context_object_name = "vouchers"
    template_name = "oscar/dashboard/vouchers/voucher_set_detail.html"
    form_class = VoucherSetSearchForm
    paginate_by = 50

    def dispatch(self, request, *args, **kwargs):
        self.voucher_set = get_object_or_404(VoucherSet, pk=kwargs["pk"])
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        self.search_filters = []
        qs = self.model.objects.filter(voucher_set=self.voucher_set).order_by(
            "-date_created"
        )

        qs = sort_queryset(
            qs,
            self.request,
            ["num_basket_additions", "num_orders", "date_created"],
            "-date_created",
        )

        # If form not submitted, return early
        is_form_submitted = "name" in self.request.GET or "code" in self.request.GET
        if not is_form_submitted:
            self.form = self.form_class()
            return qs

        self.form = self.form_class(self.request.GET)
        if not self.form.is_valid():
            return qs

        data = self.form.cleaned_data
        if data["code"]:
            qs = qs.filter(code__icontains=data["code"])
            self.search_filters.append(_('Code matches "%s"') % data["code"])

        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["voucher_set"] = self.voucher_set
        ctx["form"] = self.form
        ctx["search_filters"] = self.search_filters
        return ctx


class VoucherSetListView(generic.ListView):
    model = VoucherSet
    context_object_name = "voucher_sets"
    template_name = "oscar/dashboard/vouchers/voucher_set_list.html"
    paginate_by = settings.OSCAR_DASHBOARD_ITEMS_PER_PAGE

    def get_queryset(self):
        qs = self.model.objects.all().order_by("-date_created")
        qs = sort_queryset(
            qs,
            self.request,
            ["num_basket_additions", "num_orders", "date_created"],
            "-date_created",
        )
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        description = _("Voucher sets")
        ctx["description"] = description
        return ctx


class VoucherSetDownloadView(generic.DetailView):
    template_name = "oscar/dashboard/vouchers/voucher_set_form.html"
    model = VoucherSet
    form_class = VoucherSetForm

    def get(self, request, *args, **kwargs):
        voucher_set = self.get_object()

        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = 'attachment; filename="%s.csv"' % slugify(
            voucher_set.name
        )

        writer = csv.writer(response)
        for code in voucher_set.vouchers.values_list("code", flat=True):
            writer.writerow([code])

        return response


class VoucherSetDeleteView(generic.DeleteView):
    model = VoucherSet
    template_name = "oscar/dashboard/vouchers/voucher_set_delete.html"
    context_object_name = "voucher_set"

    def get_success_url(self):
        messages.warning(self.request, _("Voucher set deleted"))
        return reverse("dashboard:voucher-set-list")
