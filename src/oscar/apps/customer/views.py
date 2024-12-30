# pylint: disable=attribute-defined-outside-init
from django import http
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login as auth_login
from django.contrib.auth import logout as auth_logout
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.forms import PasswordChangeForm
from django.core.exceptions import ObjectDoesNotExist
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.utils.translation import gettext_lazy as _
from django.views import generic
from plans.models import Plan, UserPlan
from plans.signals import activate_user_plan
from oscar.apps.customer.utils import get_password_reset_url
from oscar.core.compat import get_user_model
from oscar.core.loading import get_class, get_classes, get_model, get_profile_class
from oscar.core.utils import safe_referrer
from oscar.views.generic import PostActionMixin
from django import forms
from django.core.exceptions import PermissionDenied
from plans.plan_change import StandardPlanChangePolicy
from decimal import Decimal

PageTitleMixin, RegisterUserMixin = get_classes(
    "customer.mixins", ["PageTitleMixin", "RegisterUserMixin"]
)
CustomerDispatcher = get_class("customer.utils", "CustomerDispatcher")
EmailAuthenticationForm, EmailUserCreationForm, OrderSearchForm = get_classes(
    "customer.forms",
    ["EmailAuthenticationForm", "EmailUserCreationForm", "OrderSearchForm"],
)
ProfileForm, ConfirmPasswordForm = get_classes(
    "customer.forms", ["ProfileForm", "ConfirmPasswordForm"]
)
UserAddressForm = get_class("address.forms", "UserAddressForm")
Order = get_model("order", "Order")
UserAddress = get_model("address", "UserAddress")
Email = get_model("communication", "Email")

User = get_user_model()


# =======
# Account
# =======


class AccountSummaryView(generic.RedirectView):
    """
    View that exists for legacy reasons and customisability. It commonly gets
    called when the user clicks on "Account" in the navbar.

    Oscar defaults to just redirecting to the profile summary page (and
    that redirect can be configured via OSCAR_ACCOUNT_REDIRECT_URL), but
    it's also likely you want to display an 'account overview' page or
    such like. The presence of this view allows just that, without
    having to change a lot of templates.
    """

    pattern_name = settings.OSCAR_ACCOUNTS_REDIRECT_URL
    permanent = False


class AccountRegistrationView(RegisterUserMixin, generic.FormView):
    form_class = EmailUserCreationForm
    template_name = "oscar/customer/registration.html"
    redirect_field_name = "next"

    def get(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect(settings.LOGIN_REDIRECT_URL)
        return super().get(request, *args, **kwargs)

    def get_logged_in_redirect(self):
        return reverse("customer:summary")

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["initial"] = {
            "email": self.request.GET.get("email", ""),
            "redirect_url": self.request.GET.get(self.redirect_field_name, ""),
        }
        kwargs["host"] = self.request.get_host()
        return kwargs

    def get_context_data(self, *args, **kwargs):
        ctx = super().get_context_data(*args, **kwargs)
        ctx["cancel_url"] = safe_referrer(self.request, "")
        return ctx

    def form_valid(self, form):
        self.register_user(form)
        return redirect(form.cleaned_data["redirect_url"])


class AccountAuthView(RegisterUserMixin, generic.TemplateView):
    """
    This is actually a slightly odd double form view that allows a customer to
    either login or register.
    """

    template_name = "oscar/customer/login_registration.html"
    login_prefix, registration_prefix = "login", "registration"
    login_form_class = EmailAuthenticationForm
    registration_form_class = EmailUserCreationForm
    redirect_field_name = "next"

    def get(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect(settings.LOGIN_REDIRECT_URL)
        return super().get(request, *args, **kwargs)

    def get_context_data(self, *args, **kwargs):
        ctx = super().get_context_data(*args, **kwargs)
        if "login_form" not in kwargs:
            ctx["login_form"] = self.get_login_form()
        if "registration_form" not in kwargs:
            ctx["registration_form"] = self.get_registration_form()
        return ctx

    def post(self, request, *args, **kwargs):
        # Use the name of the submit button to determine which form to validate
        if "login_submit" in request.POST:
            return self.validate_login_form()
        elif "registration_submit" in request.POST:
            return self.validate_registration_form()
        return http.HttpResponseBadRequest()

    # LOGIN

    def get_login_form(self, bind_data=False):
        return self.login_form_class(**self.get_login_form_kwargs(bind_data))

    def get_login_form_kwargs(self, bind_data=False):
        kwargs = {}
        kwargs["request"] = self.request
        kwargs["host"] = self.request.get_host()
        kwargs["prefix"] = self.login_prefix
        kwargs["initial"] = {
            "redirect_url": self.request.GET.get(self.redirect_field_name, ""),
        }
        if bind_data and self.request.method in ("POST", "PUT"):
            kwargs.update(
                {
                    "data": self.request.POST,
                    "files": self.request.FILES,
                }
            )
        return kwargs

    def validate_login_form(self):
        form = self.get_login_form(bind_data=True)
        if form.is_valid():
            user = form.get_user()

            # Grab a reference to the session ID before logging in
            old_session_key = self.request.session.session_key

            auth_login(self.request, form.get_user())

            # Raise signal robustly (we don't want exceptions to crash the
            # request handling). We use a custom signal as we want to track the
            # session key before calling login (which cycles the session ID).
            signals.user_logged_in.send_robust(
                sender=self,
                request=self.request,
                user=user,
                old_session_key=old_session_key,
            )

            msg = self.get_login_success_message(form)
            if msg:
                messages.success(self.request, msg)

            return redirect(self.get_login_success_url(form))

        ctx = self.get_context_data(login_form=form)
        return self.render_to_response(ctx)

    # pylint: disable=unused-argument
    def get_login_success_message(self, form):
        return _("Welcome back")

    def get_login_success_url(self, form):
        redirect_url = form.cleaned_data["redirect_url"]
        if redirect_url:
            return redirect_url

        # Redirect staff members to dashboard as that's the most likely place
        # they'll want to visit if they're logging in.
        if self.request.user.is_staff:
            return reverse("dashboard:index")

        return settings.LOGIN_REDIRECT_URL

    # REGISTRATION

    def get_registration_form(self, bind_data=False):
        return self.registration_form_class(
            **self.get_registration_form_kwargs(bind_data)
        )

    def get_registration_form_kwargs(self, bind_data=False):
        kwargs = {}
        kwargs["host"] = self.request.get_host()
        kwargs["prefix"] = self.registration_prefix
        kwargs["initial"] = {
            "redirect_url": self.request.GET.get(self.redirect_field_name, ""),
        }
        if bind_data and self.request.method in ("POST", "PUT"):
            kwargs.update(
                {
                    "data": self.request.POST,
                    "files": self.request.FILES,
                }
            )
        return kwargs

    def validate_registration_form(self):
        form = self.get_registration_form(bind_data=True)
        if form.is_valid():
            self.register_user(form)

            msg = self.get_registration_success_message(form)
            messages.success(self.request, msg)

            return redirect(self.get_registration_success_url(form))

        ctx = self.get_context_data(registration_form=form)
        return self.render_to_response(ctx)

    # pylint: disable=unused-argument
    def get_registration_success_message(self, form):
        return _("Thanks for registering!")

    def get_registration_success_url(self, form):
        redirect_url = form.cleaned_data["redirect_url"]
        if redirect_url:
            return redirect_url

        return settings.LOGIN_REDIRECT_URL


class LogoutView(generic.RedirectView):
    url = settings.OSCAR_HOMEPAGE
    permanent = False

    def get(self, request, *args, **kwargs):
        auth_logout(request)
        response = super().get(request, *args, **kwargs)

        for cookie in settings.OSCAR_COOKIES_DELETE_ON_LOGOUT:
            response.delete_cookie(cookie)

        return response


# =============
# Profile
# =============


class ProfileView(PageTitleMixin, generic.TemplateView):
    template_name = "oscar/customer/profile/profile.html"
    page_title = _("Profile")
    active_tab = "profile"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["profile_fields"] = self.get_profile_fields(self.request.user)
        return ctx

    def get_profile_fields(self, user):
        field_data = []

        # Check for custom user model
        for field_name in User._meta.additional_fields:
            field_data.append(self.get_model_field_data(user, field_name))

        # Check for profile class
        profile_class = get_profile_class()
        if profile_class:
            try:
                profile = profile_class.objects.get(user=user)
            except ObjectDoesNotExist:
                profile = profile_class(user=user)

            field_names = [f.name for f in profile._meta.local_fields]
            for field_name in field_names:
                if field_name in ("user", "id"):
                    continue
                field_data.append(self.get_model_field_data(profile, field_name))

        return field_data

    def get_model_field_data(self, model_class, field_name):
        """
        Extract the verbose name and value for a model's field value
        """
        field = model_class._meta.get_field(field_name)
        if field.choices:
            value = getattr(model_class, "get_%s_display" % field_name)()
        else:
            value = getattr(model_class, field_name)
        return {
            "name": getattr(field, "verbose_name"),
            "value": value,
        }


class ProfileUpdateView(PageTitleMixin, generic.FormView):
    form_class = ProfileForm
    template_name = "oscar/customer/profile/profile_form.html"
    page_title = _("Edit Profile")
    active_tab = "profile"
    success_url = reverse_lazy("customer:profile-view")

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def form_valid(self, form):
        # Grab current user instance before we save form.  We may need this to
        # send a warning email if the email address is changed.
        try:
            old_user = User.objects.get(id=self.request.user.id)
        except User.DoesNotExist:
            old_user = None

        form.save()

        # We have to look up the email address from the form's
        # cleaned data because the object created by form.save() can
        # either be a user or profile instance depending whether a profile
        # class has been specified by the AUTH_PROFILE_MODULE setting.
        new_email = form.cleaned_data.get("email")
        if new_email and old_user and new_email != old_user.email:
            # Email address has changed - send a confirmation email to the old
            # address including a password reset link in case this is a
            # suspicious change.
            self.send_email_changed_email(old_user, new_email)

        messages.success(self.request, _("Profile updated"))
        return redirect(self.get_success_url())

    def send_email_changed_email(self, old_user, new_email):
        user = self.request.user
        extra_context = {
            "user": user,
            "reset_url": get_password_reset_url(user),
            "new_email": new_email,
            "request": self.request,
        }
        CustomerDispatcher().send_email_changed_email_for_user(old_user, extra_context)


class ProfileDeleteView(PageTitleMixin, generic.FormView):
    form_class = ConfirmPasswordForm
    template_name = "oscar/customer/profile/profile_delete.html"
    page_title = _("Delete profile")
    active_tab = "profile"
    success_url = settings.OSCAR_HOMEPAGE

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def form_valid(self, form):
        self.request.user.delete()
        messages.success(
            self.request,
            _("Your profile has now been deleted. Thanks for using the site."),
        )
        return redirect(self.get_success_url())


class ChangePasswordView(PageTitleMixin, generic.FormView):
    form_class = PasswordChangeForm
    template_name = "oscar/customer/profile/change_password_form.html"
    page_title = _("Change Password")
    active_tab = "profile"
    success_url = reverse_lazy("customer:profile-view")

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def form_valid(self, form):
        form.save()
        update_session_auth_hash(self.request, self.request.user)
        messages.success(self.request, _("Password updated"))

        self.send_password_changed_email()

        return redirect(self.get_success_url())

    def send_password_changed_email(self):
        user = self.request.user
        extra_context = {
            "user": user,
            "reset_url": get_password_reset_url(self.request.user),
            "request": self.request,
        }
        CustomerDispatcher().send_password_changed_email_for_user(user, extra_context)

# =============
# Subscriptions
# =============


class SubscriptionsListView(PageTitleMixin, generic.TemplateView):
    template_name = "oscar/customer/subscription/subscription.html"
    page_title = _("Subscriptions")
    active_tab = "subscriptions"

    def get_context_data(self, **kwargs):
        user = self.request.user
        ctx = super().get_context_data(**kwargs)
        ctx["currency"] =  settings.PLANS_CURRENCY
        ctx["available_plans"] = Plan.objects.filter(available=True)
        try:
            ctx["current_plan"] = user.userplan.plan
            ctx["current_plan_active"] = user.userplan.is_active()
            ctx["current_plan_expired"] = user.userplan.is_expired()
            ctx["expiration_date"] = user.userplan.expire
        except:
            ctx["current_plan"] = None
        return ctx

class CancelSubscriptionView(PageTitleMixin, generic.TemplateView):
    template_name = "oscar/customer/subscription/cancel-subscription.html"
    page_title = _("Subscriptions")
    active_tab = "subscriptions"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["action"] =  reverse_lazy("customer:cancel-subscription")
        try:
            ctx["current_plan"] = Plan.get_current_plan(self.request.user)
            ctx["expiration_date"] = self.request.user.userplan.expire
        except:
            ctx["current_plan"] = None
        return ctx


class CancelSubscriptionForm(forms.Form):

    def __init__(self, user, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user

    def clean(self):
        cleaned_data = super().clean()
        
        try:
            user_plan = Plan.get_current_plan(self.user)
        except:
            raise forms.ValidationError(_("You don't have an active subscription to cancel."))
        
        return cleaned_data

class CancelSubscription(PageTitleMixin, generic.FormView):
    template_name = "oscar/customer/subscription/cancel-subscription.html"
    form_class = CancelSubscriptionForm
    page_title = _("Cancel Subscription")
    active_tab = "subscriptions"
    success_url = reverse_lazy("customer:subscription-view")

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        try:
            user_plan = Plan.get_current_plan(self.request.user)
            ctx["current_plan"] = user_plan
            ctx["expiration_date"] = self.request.user.userplan.expire
        except UserPlan.DoesNotExist:
            ctx["current_plan"] = None
            ctx["expiration_date"] = None
        return ctx
        
    def post(self, request, *args, **kwargs):
        form = self.get_form()
        if form.is_valid():
            return self.form_valid(form)
        return self.form_invalid(form)

    def form_valid(self, form):
        try:            
            # Cancel the subscription
            self.request.user.userplan.deactivate()

            messages.success(
                self.request,
                _("Your subscription has been successfully cancelled.")
            )
            return redirect(self.get_success_url())
        except UserPlan.DoesNotExist:
            messages.error(
                self.request,
                _("Unable to cancel subscription. No active subscription found.")
            )
            return redirect("customer:subscription-view")
        except Exception as e:
            messages.error(
                self.request,
                _("An error occurred while cancelling your subscription. Please try again.")
            )
            return self.form_invalid(form)

        return super().form_valid(form)

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('customer:login')
        return super().dispatch(request, *args, **kwargs)

class ReactivateSubscriptionForm(forms.Form):

    def __init__(self, user, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user

    def clean(self):
        cleaned_data = super().clean()
        try:
            user_plan = Plan.get_current_plan(self.user)
        except:
            raise forms.ValidationError(_("You don't have canceled subscription to activate."))
        
        return cleaned_data

class ReactivateSubscriptionView(PageTitleMixin, generic.FormView):
    template_name = "oscar/customer/subscription/subscription.html"
    form_class = ReactivateSubscriptionForm
    page_title = _("Reactivate Subscription")
    active_tab = "subscriptions"
    success_url = reverse_lazy("customer:subscription-view")

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        try:
            user_plan = Plan.get_current_plan(self.request.user)
            ctx["current_plan"] = user_plan
            ctx["expiration_date"] = self.request.user.userplan.expire
        except UserPlan.DoesNotExist:
            ctx["current_plan"] = None
            ctx["expiration_date"] = None
        return ctx
        
    def post(self, request, *args, **kwargs):
        form = self.get_form()
        if form.is_valid():
            return self.form_valid(form)
        return self.form_invalid(form)

    def form_valid(self, form):
        try:            
            # Cancel the subscription
            self.request.user.userplan.activate()

            messages.success(
                self.request,
                _("Your subscription has been successfully Activated.")
            )
            return redirect(self.get_success_url())
        except UserPlan.DoesNotExist:
            messages.error(
                self.request,
                _("Unable to reactivate subscription. No subscription found.")
            )
            return redirect("customer:subscription-view")
        except Exception as e:
            messages.error(
                self.request,
                _("An error occurred while activating your subscription. Please try again.")
            )
            return self.form_invalid(form)

        return super().form_valid(form)

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('customer:login')
        return super().dispatch(request, *args, **kwargs)

class SubscribeView(PageTitleMixin, generic.View):
    template_name = "oscar/customer/subscription/subscribe-confirmation.html"
    page_title = _("Subscribe to Plan")
    active_tab = "subscriptions"
    success_url = reverse_lazy("customer:subscription-view")

    def get(self, request, *args, **kwargs):
        plan_id = request.GET.get('plan_id')
        if not plan_id:
            messages.error(request, _("No plan selected."))
            return redirect(self.success_url)

        try:
            plan = Plan.objects.get(id=plan_id)
            context = self.get_context_data(plan)
            return render(request, self.template_name, context)
        except Plan.DoesNotExist:
            messages.error(request, _("Selected plan does not exist."))
            return redirect(self.success_url)

    def get_context_data(self, plan):
        return {
            'page_title': self.page_title,
            'active_tab': self.active_tab,
            'plan': plan,
            'currency': 'USD'  # You might want to make this dynamic
        }

    def post(self, request, *args, **kwargs):
        plan_id = request.POST.get('plan_id')
        branches = int(request.POST.get('branches', 1))
        if not plan_id:
            messages.error(request, _("No plan selected."))
            return redirect(self.success_url)
            
        if branches < 1:
            messages.error(request, _("Number of branches must be at least 1."))
            return redirect(request.path)
            
        try:
            # Get the selected plan
            plan = Plan.objects.get(id=plan_id)
            user = request.user

            # Calculate total price
            total_price = plan.price() * Decimal(branches)
            
            # Check if user already has an active subscription
            existing_plan = UserPlan.objects.filter(
                user=user,
            ).first()
            
            if existing_plan:
                messages.error(
                    request,
                    _("You already have a subscription. Please activate it.")
                )
                return redirect(self.success_url)

            payment = True #placeholder
            if payment:
                # Create new user plan
                user_plan = UserPlan.objects.create(
                    user=user,
                    plan=plan,
                    active=False,
                    branches=branches  
                )
                
                activate_user_plan.send(
                    sender=self,
                    user=user
                )
                
                messages.success(
                    request,
                    _("Successfully subscribed to {} with {} branches for {} {}").format(
                        plan.name,
                        branches,
                        total_price,
                        'USD'
                    )
                )

        except Plan.DoesNotExist:
            messages.error(request, _("Selected plan does not exist."))
        except ValueError:
            messages.error(request, _("Invalid number of branches provided."))
        except Exception as e:
            print(e)
            messages.error(
                request,
                _("An error occurred while processing your subscription. Please try again.")
            )
            
        return redirect(self.success_url)

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('customer:login')
        return super().dispatch(request, *args, **kwargs)

class ChangeSubscriptionView(PageTitleMixin, generic.View):
    template_name = "oscar/customer/subscription/change-subscription.html"
    page_title = _("Change Subscription")
    active_tab = "subscriptions"
    success_url = reverse_lazy("customer:subscription-view")

    def get(self, request, *args, **kwargs):
        plan_id = request.GET.get('plan_id')
        if not plan_id:
            messages.error(request, _("No plan selected for change."))
            return redirect(self.success_url)

        try:
            new_plan = Plan.objects.get(id=plan_id)
            context = self.get_context_data(new_plan)
            return render(request, self.template_name, context)
        except Plan.DoesNotExist:
            messages.error(request, _("Selected plan does not exist."))
            return redirect(self.success_url)

    def get_context_data(self, new_plan):
        context = {
            'page_title': self.page_title,
            'active_tab': self.active_tab,
            'new_plan': new_plan,
            'currency': settings.PLANS_CURRENCY
        }
        
        try:
            current_plan = self.request.user.userplan
            context.update({
                'current_plan': current_plan.plan,
                'current_branches': current_plan.branches,
                'expiration_date': current_plan.expire,
                'change_price': StandardPlanChangePolicy().get_change_price(
                    current_plan.plan,
                    new_plan,
                    current_plan.days_left()
                )
            })
        except UserPlan.DoesNotExist:
            context.update({
                'current_plan': None,
                'expiration_date': None
            })
            
        return context

    def post(self, request, *args, **kwargs):
        new_plan_id = request.POST.get('plan_id')
        branches = int(request.POST.get('branches', 1))
        
        if not new_plan_id:
            messages.error(request, _("No plan selected for change."))
            return redirect(self.success_url)
            
        if branches < 1:
            messages.error(request, _("Number of branches must be at least 1."))
            return redirect(request.path)
            
        try:
            # Get current and new plans
            current_plan = request.user.userplan
            new_plan = Plan.objects.get(id=new_plan_id)
            
            if current_plan.plan.id == new_plan.id:
                messages.error(request, _("This is already your current plan."))
                return redirect(self.success_url)
            
            # Calculate base price using StandardPlanChangePolicy
            policy = StandardPlanChangePolicy()
            days_left = current_plan.days_left()
            base_change_price = policy.get_change_price(current_plan.plan, new_plan, days_left)
            
            # Calculate total price with branches
            if base_change_price is not None:
                total_change_price = Decimal(str(base_change_price)) * Decimal(str(branches))
            else:
                total_change_price = None
                        
            if total_change_price is None:
                current_plan.extend_account(new_plan, None)
                messages.success(
                    request,
                    _("Successfully changed to plan {} for {} branches").format(
                        new_plan.name,
                        branches
                    )
                )
            else:
                # Here you would typically:
                # 1. Create an order for the total_change_price amount
                # 2. Redirect to payment
                # For this example, we'll assume immediate payment success
                payment = True
                if payment:
                    current_plan.extend_account(new_plan, None)
                    # You might want to store the number of branches in your UserPlan model
                    current_plan.branches = branches
                    current_plan.save()
                    messages.success(
                        request,
                        _("Successfully upgraded to plan {} for {} branches. Total cost: {} {}").format(
                            new_plan.name,
                            branches,
                            total_change_price,
                            'USD'  # You might want to make this dynamic
                        )
                    )
                
        except UserPlan.DoesNotExist:
            messages.error(request, _("You don't have an active subscription to change."))
        except Plan.DoesNotExist:
            messages.error(request, _("Selected plan does not exist."))
        except ValueError as e:
            messages.error(request, _("Invalid number of branches provided."))
        except Exception as e:
            print(e)
            messages.error(
                request,
                _("An error occurred while changing your plan. Please try again.")
            )
        
        return redirect(self.success_url)

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('customer:login')
        return super().dispatch(request, *args, **kwargs)

class RenewSubscriptionView(PageTitleMixin, generic.View):
    success_url = reverse_lazy("customer:subscription-view")

    def post(self, request, *args, **kwargs):
        try:
            # Get the expired plan
            expired_plan = request.user.userplan
            expired_plan.expire = None
            expired_plan.save()

            payment = True
            if payment :
                # Send activation signal
                activate_user_plan.send(
                    sender=self,
                    user=request.user
                )
                
                messages.success(
                    request,
                    _("Your subscription has been successfully renewed.")
                )
            
        except UserPlan.DoesNotExist:
            messages.error(
                request,
                _("Unable to find the expired subscription to renew.")
            )
            return redirect(self.success_url)
        except Exception as e:
            print(e)
            messages.error(
                request,
                _("An error occurred while renewing your subscription. Please try again.")
            )
            return redirect(self.success_url)
            
        return redirect(self.success_url)

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('customer:login')
        return super().dispatch(request, *args, **kwargs)
# =============
# Email history
# =============


class EmailHistoryView(PageTitleMixin, generic.ListView):
    context_object_name = "emails"
    template_name = "oscar/communication/email/email_list.html"
    paginate_by = settings.OSCAR_EMAILS_PER_PAGE
    page_title = _("Email History")
    active_tab = "emails"

    def get_queryset(self):
        """
        Return Queryset of :py:class:`Email <oscar.apps.customer.abstract_models.AbstractEmail>`
        instances, that has been sent to the currently authenticated user.
        """
        return Email._default_manager.filter(user=self.request.user)


class EmailDetailView(PageTitleMixin, generic.DetailView):
    """Customer email"""

    template_name = "oscar/communication/email/email_detail.html"
    context_object_name = "email"
    active_tab = "emails"

    def get_object(self, queryset=None):
        return get_object_or_404(
            Email, user=self.request.user, id=self.kwargs["email_id"]
        )

    def get_page_title(self):
        """Append email subject to page title"""
        return "%s: %s" % (_("Email"), self.object.subject)


# =============
# Order history
# =============


class OrderHistoryView(PageTitleMixin, generic.ListView):
    """
    Customer order history
    """

    context_object_name = "orders"
    template_name = "oscar/customer/order/order_list.html"
    paginate_by = settings.OSCAR_ORDERS_PER_PAGE
    model = Order
    form_class = OrderSearchForm
    page_title = _("Order History")
    active_tab = "orders"

    def get(self, request, *args, **kwargs):
        if "date_from" in request.GET:
            self.form = self.form_class(self.request.GET)
            if not self.form.is_valid():
                self.object_list = self.get_queryset()
                ctx = self.get_context_data(object_list=self.object_list)
                return self.render_to_response(ctx)
            data = self.form.cleaned_data

            # If the user has just entered an order number, try and look it up
            # and redirect immediately to the order detail page.
            if data["order_number"] and not (data["date_to"] or data["date_from"]):
                try:
                    order = Order.objects.get(
                        number=data["order_number"], user=self.request.user
                    )
                except Order.DoesNotExist:
                    pass
                else:
                    return redirect("customer:order", order_number=order.number)
        else:
            self.form = self.form_class()
        return super().get(request, *args, **kwargs)

    def get_queryset(self):
        """
        Return Queryset of :py:class:`Order <oscar.apps.order.abstract_models.AbstractOrder>`
        instances for the currently authenticated user.
        """
        qs = self.model._default_manager.filter(user=self.request.user)
        if self.form.is_bound and self.form.is_valid():
            qs = qs.filter(**self.form.get_filters())
        return qs

    def get_context_data(self, *args, **kwargs):
        ctx = super().get_context_data(*args, **kwargs)
        ctx["form"] = self.form
        return ctx


class OrderDetailView(PageTitleMixin, PostActionMixin, generic.DetailView):
    model = Order
    active_tab = "orders"

    def get_template_names(self):
        return ["oscar/customer/order/order_detail.html"]

    def get_page_title(self):
        """
        Order number as page title
        """
        return "%s #%s" % (_("Order"), self.object.number)

    def get_object(self, queryset=None):
        return get_object_or_404(
            self.model, user=self.request.user, number=self.kwargs["order_number"]
        )

    def do_reorder(self, order):
        """
        'Re-order' a previous order.

        This puts the contents of the previous order into your basket
        """
        # Collect lines to be added to the basket and any warnings for lines
        # that are no longer available.
        basket = self.request.basket
        lines_to_add = []
        warnings = []
        for line in order.lines.all():
            is_available, reason = line.is_available_to_reorder(
                basket, self.request.strategy
            )
            if is_available:
                lines_to_add.append(line)
            else:
                warnings.append(reason)

        # Check whether the number of items in the basket won't exceed the
        # maximum.
        total_quantity = sum([line.quantity for line in lines_to_add])
        is_quantity_allowed, reason = basket.is_quantity_allowed(total_quantity)
        if not is_quantity_allowed:
            messages.warning(self.request, reason)
            self.response = redirect("customer:order-list")
            return

        # Add any warnings
        for warning in warnings:
            messages.warning(self.request, warning)

        for line in lines_to_add:
            options = []
            for attribute in line.attributes.all():
                if attribute.option:
                    options.append(
                        {"option": attribute.option, "value": attribute.value}
                    )
            basket.add_product(line.product, line.quantity, options)

        if len(lines_to_add) > 0:
            self.response = redirect("basket:summary")
            messages.info(
                self.request,
                _(
                    "All available lines from order %(number)s "
                    "have been added to your basket"
                )
                % {"number": order.number},
            )
        else:
            self.response = redirect("customer:order-list")
            messages.warning(
                self.request,
                _(
                    "It is not possible to re-order order %(number)s "
                    "as none of its lines are available to purchase"
                )
                % {"number": order.number},
            )


class OrderLineView(PostActionMixin, generic.DetailView):
    """Customer order line"""

    def get_object(self, queryset=None):
        order = get_object_or_404(
            Order, user=self.request.user, number=self.kwargs["order_number"]
        )
        return order.lines.get(id=self.kwargs["line_id"])

    def do_reorder(self, line):
        self.response = redirect("customer:order", self.kwargs["order_number"])
        basket = self.request.basket

        line_available_to_reorder, reason = line.is_available_to_reorder(
            basket, self.request.strategy
        )

        if not line_available_to_reorder:
            messages.warning(self.request, reason)
            return

        # We need to pass response to the get_or_create... method
        # as a new basket might need to be created
        self.response = redirect("basket:summary")

        # Convert line attributes into basket options
        options = []
        for attribute in line.attributes.all():
            if attribute.option:
                options.append({"option": attribute.option, "value": attribute.value})
        basket.add_product(line.product, line.quantity, options)

        if line.quantity > 1:
            msg = _(
                "%(qty)d copies of '%(product)s' have been added to your basket"
            ) % {"qty": line.quantity, "product": line.product}
        else:
            msg = _("'%s' has been added to your basket") % line.product

        messages.info(self.request, msg)


class AnonymousOrderDetailView(generic.DetailView):
    model = Order
    template_name = "oscar/customer/anon_order.html"

    def get_object(self, queryset=None):
        # Check URL hash matches that for order to prevent spoof attacks
        order = get_object_or_404(
            self.model, user=None, number=self.kwargs["order_number"]
        )
        if not order.check_verification_hash(self.kwargs["hash"]):
            raise http.Http404()
        return order


# ------------
# Address book
# ------------


class AddressListView(PageTitleMixin, generic.ListView):
    """Customer address book"""

    context_object_name = "addresses"
    template_name = "oscar/customer/address/address_list.html"
    paginate_by = settings.OSCAR_ADDRESSES_PER_PAGE
    active_tab = "addresses"
    page_title = _("Address Book")

    def get_queryset(self):
        """Return customer's addresses"""
        return UserAddress._default_manager.filter(user=self.request.user)


class AddressCreateView(PageTitleMixin, generic.CreateView):
    form_class = UserAddressForm
    model = UserAddress
    template_name = "oscar/customer/address/address_form.html"
    active_tab = "addresses"
    page_title = _("Add a new address")
    success_url = reverse_lazy("customer:address-list")

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["title"] = _("Add a new address")
        return ctx

    def get_success_url(self):
        messages.success(self.request, _("Address '%s' created") % self.object.summary)
        return super().get_success_url()


class AddressUpdateView(PageTitleMixin, generic.UpdateView):
    form_class = UserAddressForm
    model = UserAddress
    template_name = "oscar/customer/address/address_form.html"
    active_tab = "addresses"
    page_title = _("Edit address")
    success_url = reverse_lazy("customer:address-list")

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["title"] = _("Edit address")
        return ctx

    def get_queryset(self):
        return self.request.user.addresses.all()

    def get_success_url(self):
        messages.success(self.request, _("Address '%s' updated") % self.object.summary)
        return super().get_success_url()


class AddressDeleteView(PageTitleMixin, generic.DeleteView):
    model = UserAddress
    template_name = "oscar/customer/address/address_delete.html"
    page_title = _("Delete address?")
    active_tab = "addresses"
    context_object_name = "address"
    success_url = reverse_lazy("customer:address-list")

    def get_queryset(self):
        return UserAddress._default_manager.filter(user=self.request.user)

    def get_success_url(self):
        messages.success(self.request, _("Address '%s' deleted") % self.object.summary)
        return super().get_success_url()


class AddressChangeStatusView(generic.RedirectView):
    """
    Sets an address as default_for_(billing|shipping)
    """

    url = reverse_lazy("customer:address-list")
    permanent = False

    def get(self, request, *args, pk=None, action=None, **kwargs):
        address = get_object_or_404(UserAddress, user=self.request.user, pk=pk)
        #  We don't want the user to set an address as the default shipping
        #  address, though they should be able to set it as their billing
        #  address.
        if address.country.is_shipping_country:
            setattr(address, "is_%s" % action, True)
        elif action == "default_for_billing":
            setattr(address, "is_default_for_billing", True)
        else:
            messages.error(request, _("We do not ship to this country"))
        address.save()
        return super().get(request, *args, **kwargs)
