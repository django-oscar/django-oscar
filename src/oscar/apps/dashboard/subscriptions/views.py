# Python Standard Library
import datetime
from decimal import Decimal

# Django Core
from django import forms, http
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login as auth_login, logout as auth_logout, update_session_auth_hash
from django.core.exceptions import ObjectDoesNotExist, PermissionDenied
from django.http import Http404, HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.utils.translation import gettext_lazy as _
from django.views import generic

# Third-party Apps
from plans.models import Plan, UserPlan
from plans.signals import activate_user_plan
from plans.plan_change import StandardPlanChangePolicy



class SubscriptionsListView(generic.TemplateView):
    template_name = "oscar/dashboard/subscription/subscription.html"


    def get_context_data(self, **kwargs):
        user = self.request.user
        ctx = super().get_context_data(**kwargs)
        ctx["currency"] =  settings.PLANS_CURRENCY
        if hasattr(user, "vendor"):
            ctx["available_plans"] = Plan.objects.filter(available=True, plan_for="vendors").order_by("-order")
        else:
            ctx["available_plans"] = Plan.objects.filter(available=True, plan_for="schools")
        try:
            ctx["current_plan"] = user.userplan.plan
            ctx["current_plan_active"] = user.userplan.is_active()
            ctx["current_plan_expired"] = user.userplan.is_expired()
            ctx["expiration_date"] = user.userplan.expire
        except:
            ctx["current_plan"] = None
        return ctx

class CancelSubscriptionView( generic.TemplateView):
    template_name = "oscar/dashboard/subscription/cancel-subscription.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["action"] =  reverse_lazy("dashboard:cancel-subscription")
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

class CancelSubscription( generic.FormView):
    template_name = "oscar/dashboard/subscription/cancel-subscription.html"
    form_class = CancelSubscriptionForm
    success_url = reverse_lazy("dashboard:subscription-view")

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
            return redirect("dashboard:subscription-view")
        except Exception as e:
            messages.error(
                self.request,
                _("An error occurred while cancelling your subscription. Please try again.")
            )
            return self.form_invalid(form)

        return super().form_valid(form)

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('dashboard:login')
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

class ReactivateSubscriptionView( generic.FormView):
    template_name = "oscar/dashboard/subscription/subscription.html"
    form_class = ReactivateSubscriptionForm
    success_url = reverse_lazy("dashboard:subscription-view")

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
            return redirect("dashboard:subscription-view")
        except Exception as e:
            messages.error(
                self.request,
                _("An error occurred while activating your subscription. Please try again.")
            )
            return self.form_invalid(form)

        return super().form_valid(form)

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('dashboard:login')
        return super().dispatch(request, *args, **kwargs)

class SubscribeView( generic.View):
    template_name = "oscar/dashboard/subscription/subscribe-confirmation.html"
    success_url = reverse_lazy("dashboard:subscription-view")

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
            return redirect('dashboard:login')
        return super().dispatch(request, *args, **kwargs)

class ChangeSubscriptionView( generic.View):
    template_name = "oscar/dashboard/subscription/change-subscription.html"
    success_url = reverse_lazy("dashboard:subscription-view")

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
            return redirect('dashboard:login')
        return super().dispatch(request, *args, **kwargs)

class RenewSubscriptionView( generic.View):
    success_url = reverse_lazy("dashboard:subscription-view")

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
            return redirect('dashboard:login')
        return super().dispatch(request, *args, **kwargs)
