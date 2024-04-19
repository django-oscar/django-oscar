# pylint: disable=attribute-defined-outside-init
from django.contrib import messages
from django.contrib.auth.models import Permission
from django.shortcuts import get_object_or_404, redirect
from django.template.loader import render_to_string
from django.urls import reverse, reverse_lazy
from django.utils.translation import gettext_lazy as _
from django.views import generic

from oscar.apps.customer.utils import normalise_email
from oscar.core.compat import get_user_model
from oscar.core.loading import get_classes, get_model
from oscar.views import sort_queryset

User = get_user_model()
Partner = get_model("partner", "Partner")
(
    PartnerSearchForm,
    PartnerCreateForm,
    PartnerAddressForm,
    NewUserForm,
    UserEmailForm,
    ExistingUserForm,
) = get_classes(
    "dashboard.partners.forms",
    [
        "PartnerSearchForm",
        "PartnerCreateForm",
        "PartnerAddressForm",
        "NewUserForm",
        "UserEmailForm",
        "ExistingUserForm",
    ],
)


class PartnerListView(generic.ListView):
    model = Partner
    context_object_name = "partners"
    template_name = "oscar/dashboard/partners/partner_list.html"
    form_class = PartnerSearchForm

    def get_queryset(self):
        qs = self.model._default_manager.all()
        qs = sort_queryset(qs, self.request, ["name"])

        self.description = _("All partners")

        # We track whether the queryset is filtered to determine whether we
        # show the search form 'reset' button.
        self.is_filtered = False
        self.form = self.form_class(self.request.GET)
        if not self.form.is_valid():
            return qs

        data = self.form.cleaned_data

        if data["name"]:
            qs = qs.filter(name__icontains=data["name"])
            self.description = _("Partners matching '%s'") % data["name"]
            self.is_filtered = True

        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["queryset_description"] = self.description
        ctx["form"] = self.form
        ctx["is_filtered"] = self.is_filtered
        return ctx


class PartnerCreateView(generic.CreateView):
    model = Partner
    template_name = "oscar/dashboard/partners/partner_form.html"
    form_class = PartnerCreateForm
    success_url = reverse_lazy("dashboard:partner-list")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["title"] = _("Create new partner")
        return ctx

    def get_success_url(self):
        messages.success(
            self.request, _("Partner '%s' was created successfully.") % self.object.name
        )
        return reverse("dashboard:partner-list")


class PartnerManageView(generic.UpdateView):
    """
    This multi-purpose view renders out a form to edit the partner's details,
    the associated address and a list of all associated users.
    """

    template_name = "oscar/dashboard/partners/partner_manage.html"
    form_class = PartnerAddressForm
    success_url = reverse_lazy("dashboard:partner-list")

    def get_object(self, queryset=None):
        self.partner = get_object_or_404(Partner, pk=self.kwargs["pk"])
        address = self.partner.primary_address
        if address is None:
            address = self.partner.addresses.model(partner=self.partner)
        return address

    def get_initial(self):
        return {"name": self.partner.name}

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["partner"] = self.partner
        ctx["title"] = self.partner.name
        ctx["users"] = self.partner.users.all()
        return ctx

    def form_valid(self, form):
        messages.success(
            self.request,
            _("Partner '%s' was updated successfully.") % self.partner.name,
        )
        self.partner.name = form.cleaned_data["name"]
        self.partner.save()
        return super().form_valid(form)


class PartnerDeleteView(generic.DeleteView):
    model = Partner
    template_name = "oscar/dashboard/partners/partner_delete.html"

    def get_success_url(self):
        messages.success(
            self.request, _("Partner '%s' was deleted successfully.") % self.object.name
        )
        return reverse("dashboard:partner-list")


# =============
# Partner users
# =============


class PartnerUserCreateView(generic.CreateView):
    model = User
    template_name = "oscar/dashboard/partners/partner_user_form.html"
    form_class = NewUserForm

    def dispatch(self, request, *args, **kwargs):
        self.partner = get_object_or_404(Partner, pk=kwargs.get("partner_pk", None))
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["partner"] = self.partner
        ctx["title"] = _("Create user")
        return ctx

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["partner"] = self.partner
        return kwargs

    def get_success_url(self):
        name = self.object.get_full_name() or self.object.email
        messages.success(self.request, _("User '%s' was created successfully.") % name)
        return reverse("dashboard:partner-list")


class PartnerUserSelectView(generic.ListView):
    template_name = "oscar/dashboard/partners/partner_user_select.html"
    form_class = UserEmailForm
    context_object_name = "users"

    def dispatch(self, request, *args, **kwargs):
        self.partner = get_object_or_404(Partner, pk=kwargs.get("partner_pk", None))
        return super().dispatch(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        data = None
        if "email" in request.GET:
            data = request.GET
        self.form = self.form_class(data)
        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["partner"] = self.partner
        ctx["form"] = self.form
        return ctx

    def get_queryset(self):
        if self.form.is_valid():
            email = normalise_email(self.form.cleaned_data["email"])
            return User.objects.filter(email__icontains=email)
        else:
            return User.objects.none()


class PartnerUserLinkView(generic.View):
    def get(self, request, user_pk, partner_pk):
        # need to allow GET to make Undo link in PartnerUserUnlinkView work
        return self.post(request, user_pk, partner_pk)

    def post(self, request, user_pk, partner_pk):
        user = get_object_or_404(User, pk=user_pk)
        name = user.get_full_name() or user.email
        partner = get_object_or_404(Partner, pk=partner_pk)
        if self.link_user(user, partner):
            messages.success(
                request,
                _("User '%(name)s' was linked to '%(partner_name)s'")
                % {"name": name, "partner_name": partner.name},
            )
        else:
            messages.info(
                request,
                _("User '%(name)s' is already linked to '%(partner_name)s'")
                % {"name": name, "partner_name": partner.name},
            )
        return redirect("dashboard:partner-manage", pk=partner_pk)

    def link_user(self, user, partner):
        """
        Links a user to a partner, and adds the dashboard permission if needed.

        Returns False if the user was linked already; True otherwise.
        """
        if partner.users.filter(pk=user.pk).exists():
            return False
        partner.users.add(user)
        if not user.is_staff:
            dashboard_access_perm = Permission.objects.get(
                codename="dashboard_access", content_type__app_label="partner"
            )
            user.user_permissions.add(dashboard_access_perm)
        return True


class PartnerUserUnlinkView(generic.View):
    def unlink_user(self, user, partner):
        """
        Unlinks a user from a partner, and removes the dashboard permission
        if they are not linked to any other partners.

        Returns False if the user was not linked to the partner; True
        otherwise.
        """
        if not partner.users.filter(pk=user.pk).exists():
            return False
        partner.users.remove(user)
        if not user.is_staff and not user.partners.exists():
            dashboard_access_perm = Permission.objects.get(
                codename="dashboard_access", content_type__app_label="partner"
            )
            user.user_permissions.remove(dashboard_access_perm)
        return True

    def post(self, request, user_pk, partner_pk):
        user = get_object_or_404(User, pk=user_pk)
        name = user.get_full_name() or user.email
        partner = get_object_or_404(Partner, pk=partner_pk)
        if self.unlink_user(user, partner):
            msg = render_to_string(
                "oscar/dashboard/partners/messages/user_unlinked.html",
                {
                    "user_name": name,
                    "partner_name": partner.name,
                    "user_pk": user_pk,
                    "partner_pk": partner_pk,
                },
            )
            messages.success(self.request, msg, extra_tags="safe noicon")
        else:
            messages.error(
                request,
                _("User '%(name)s' is not linked to '%(partner_name)s'")
                % {"name": name, "partner_name": partner.name},
            )
        return redirect("dashboard:partner-manage", pk=partner_pk)


# =====
# Users
# =====


class PartnerUserUpdateView(generic.UpdateView):
    template_name = "oscar/dashboard/partners/partner_user_form.html"
    form_class = ExistingUserForm

    def get_object(self, queryset=None):
        self.partner = get_object_or_404(Partner, pk=self.kwargs["partner_pk"])
        return get_object_or_404(
            User, pk=self.kwargs["user_pk"], partners__pk=self.kwargs["partner_pk"]
        )

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        name = self.object.get_full_name() or self.object.email
        ctx["partner"] = self.partner
        ctx["title"] = _("Edit user '%s'") % name
        return ctx

    def get_success_url(self):
        name = self.object.get_full_name() or self.object.email
        messages.success(self.request, _("User '%s' was updated successfully.") % name)
        return reverse("dashboard:partner-list")
