from django.shortcuts import get_object_or_404
from django.views.generic import (TemplateView, ListView, DetailView,
                                  CreateView, UpdateView, DeleteView,
                                  FormView, RedirectView)
from django.core.urlresolvers import reverse
from django.core.exceptions import ObjectDoesNotExist
from django.http import HttpResponseRedirect, Http404
from django.contrib import messages
from django.utils.translation import ugettext as _
from django.contrib.auth import (authenticate, login as auth_login,
                                 logout as auth_logout)
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.sites.models import get_current_site
from django.conf import settings
from django.db.models import get_model

from oscar.views.generic import PostActionMixin
from oscar.apps.customer.utils import get_password_reset_url
from oscar.core.loading import get_class, get_profile_class, get_classes
from oscar.core.compat import get_user_model

Dispatcher = get_class('customer.utils', 'Dispatcher')
EmailAuthenticationForm, EmailUserCreationForm, SearchByDateRangeForm = get_classes(
    'customer.forms', ['EmailAuthenticationForm', 'EmailUserCreationForm',
                       'SearchByDateRangeForm'])
ProfileForm = get_class('customer.forms', 'ProfileForm')
UserAddressForm = get_class('address.forms', 'UserAddressForm')
user_registered = get_class('customer.signals', 'user_registered')
Order = get_model('order', 'Order')
Line = get_model('basket', 'Line')
Basket = get_model('basket', 'Basket')
UserAddress = get_model('address', 'UserAddress')
Email = get_model('customer', 'Email')
UserAddress = get_model('address', 'UserAddress')
CommunicationEventType = get_model('customer', 'CommunicationEventType')
ProductAlert = get_model('customer', 'ProductAlert')

User = get_user_model()


class LogoutView(RedirectView):
    url = '/'
    permanent = False

    def get(self, request, *args, **kwargs):
        auth_logout(request)
        response = super(LogoutView, self).get(request, *args, **kwargs)

        for cookie in settings.OSCAR_COOKIES_DELETE_ON_LOGOUT:
            response.delete_cookie(cookie)

        return response


class ProfileUpdateView(FormView):
    form_class = ProfileForm
    template_name = 'customer/profile_form.html'
    communication_type_code = 'EMAIL_CHANGED'

    def get_form_kwargs(self):
        kwargs = super(ProfileUpdateView, self).get_form_kwargs()
        kwargs['user'] = self.request.user
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
        # either be a user or profile depending on AUTH_PROFILE_MODULE
        new_email = form.cleaned_data['email']
        if old_user and new_email != old_user.email:
            # Email address has changed - send a confirmation email to the old
            # address including a password reset link in case this is a
            # suspicious change.
            ctx = {
                'user': self.request.user,
                'site': get_current_site(self.request),
                'reset_url': get_password_reset_url(old_user),
                'new_email': new_email,
            }
            msgs = CommunicationEventType.objects.get_and_render(
                code=self.communication_type_code, context=ctx)
            Dispatcher().dispatch_user_messages(old_user, msgs)

        messages.success(self.request, "Profile updated")
        return HttpResponseRedirect(self.get_success_url())

    def get_success_url(self):
        return reverse('customer:summary')


class AccountSummaryView(TemplateView):
    template_name = 'customer/profile.html'

    def get_context_data(self, **kwargs):
        ctx = super(AccountSummaryView, self).get_context_data(**kwargs)
        # Delegate data fetching to separate methods so they are easy to
        # override.
        ctx['addressbook_size'] = self.request.user.addresses.all().count()
        ctx['default_shipping_address'] = self.get_default_shipping_address(
            self.request.user)
        ctx['default_billing_address'] = self.get_default_billing_address(
            self.request.user)
        ctx['orders'] = self.get_orders(self.request.user)
        ctx['emails'] = self.get_emails(self.request.user)
        ctx['alerts'] = self.get_product_alerts(self.request.user)
        ctx['profile_fields'] = self.get_profile_fields(self.request.user)

        ctx['active_tab'] = self.request.GET.get('tab', 'profile')
        return ctx

    def get_orders(self, user):
        return Order._default_manager.filter(user=user)[0:5]

    def get_profile_fields(self, user):
        field_data = []

        # Check for custom user model
        for field_name in User._meta.additional_fields:
            field_data.append(
                self.get_model_field_data(user, field_name))

        # Check for profile class
        profile_class = get_profile_class()
        if profile_class:
            try:
                profile = profile_class.objects.get(user=user)
            except ObjectDoesNotExist:
                profile = profile_class(user=user)

            for field_name in profile._meta.get_all_field_names():
                if field_name in ('user', 'id'):
                    continue
                field_data.append(
                    self.get_model_field_data(profile, field_name))

        return field_data

    def get_model_field_data(self, model_class, field_name):
        """
        Extract the verbose name and value for a model's field value
        """
        field = model_class._meta.get_field(field_name)
        if field.choices:
            value = getattr(model_class, 'get_%s_display' % field_name)()
        else:
            value = getattr(model_class, field_name)
        return {
            'name': getattr(field, 'verbose_name'),
            'value': value,
        }

    def post(self, request, *args, **kwargs):
        # A POST means an attempt to change the status of an alert
        if 'cancel_alert' in request.POST:
            return self.cancel_alert(request.POST.get('cancel_alert'))
        return super(AccountSummaryView, self).post(request, *args, **kwargs)

    def cancel_alert(self, alert_id):
        try:
            alert = ProductAlert.objects.get(user=self.request.user, pk=alert_id)
        except ProductAlert.DoesNotExist:
            messages.error(self.request, _("No alert found"))
        else:
            alert.cancel()
            messages.success(self.request, _("Alert cancelled"))
        return HttpResponseRedirect(
            reverse('customer:summary')+'?tab=alerts'
        )

    def get_emails(self, user):
        return Email.objects.filter(user=user)

    def get_product_alerts(self, user):
        return ProductAlert.objects.select_related().filter(
            user=self.request.user,
            date_closed=None,
        )

    def get_default_billing_address(self, user):
        return self.get_user_address(user, is_default_for_billing=True)

    def get_default_shipping_address(self, user):
        return self.get_user_address(user, is_default_for_shipping=True)

    def get_user_address(self, user, **filters):
        try:
            return user.addresses.get(**filters)
        except UserAddress.DoesNotExist:
            return None


class RegisterUserMixin(object):
    communication_type_code = 'REGISTRATION'

    def register_user(self, form):
        """
        Create a user instance and send a new registration email (if configured
        to).
        """
        user = form.save()

        if getattr(settings, 'OSCAR_SEND_REGISTRATION_EMAIL', True):
            self.send_registration_email(user)

        # Raise signal
        user_registered.send_robust(sender=self, user=user)

        # We have to authenticate before login
        try:
            user = authenticate(
                username=user.email,
                password=form.cleaned_data['password1'])
        except User.MultipleObjectsReturned:
            # Handle race condition where the registration request is made
            # multiple times in quick succession.  This leads to both requests
            # passing the uniqueness check and creating users (as the first one
            # hasn't committed when the second one runs the check).  We retain
            # the first one and delete the dupes.
            users = User.objects.filter(email=user.email)
            user = users[0]
            for u in users[1:]:
                u.delete()

        auth_login(self.request, user)

        return user

    def send_registration_email(self, user):
        code = self.communication_type_code
        ctx = {'user': user,
               'site': get_current_site(self.request)}
        messages = CommunicationEventType.objects.get_and_render(
            code, ctx)
        if messages and messages['body']:
            Dispatcher().dispatch_user_messages(user, messages)


class AccountRegistrationView(FormView, RegisterUserMixin):
    form_class = EmailUserCreationForm
    template_name = 'customer/registration.html'
    redirect_field_name = 'next'

    def get(self, request, *args, **kwargs):
        if request.user.is_authenticated():
            return HttpResponseRedirect(settings.LOGIN_REDIRECT_URL)
        return super(AccountRegistrationView, self).get(
            request, *args, **kwargs)

    def get_logged_in_redirect(self):
        return reverse('customer:summary')

    def get_form_kwargs(self):
        kwargs = super(AccountRegistrationView, self).get_form_kwargs()
        kwargs['initial'] = {
            'email': self.request.GET.get('email', ''),
            'redirect_url': self.request.GET.get(self.redirect_field_name, '')
        }
        kwargs['host'] = self.request.get_host()
        return kwargs

    def get_context_data(self, *args, **kwargs):
        ctx = super(AccountRegistrationView, self).get_context_data(
            *args, **kwargs)
        ctx['cancel_url'] = self.request.META.get('HTTP_REFERER', None)
        return ctx

    def form_valid(self, form):
        self.register_user(form)
        return HttpResponseRedirect(
            form.cleaned_data['redirect_url'])


class AccountAuthView(TemplateView, RegisterUserMixin):
    """
    This is actually a slightly odd double form view
    """
    template_name = 'customer/login_registration.html'
    login_prefix, registration_prefix = 'login', 'registration'
    login_form_class = EmailAuthenticationForm
    registration_form_class = EmailUserCreationForm
    redirect_field_name = 'next'

    def get(self, request, *args, **kwargs):
        if request.user.is_authenticated():
            return HttpResponseRedirect(settings.LOGIN_REDIRECT_URL)
        return super(AccountAuthView, self).get(
            request, *args, **kwargs)

    def get_context_data(self, *args, **kwargs):
        ctx = super(AccountAuthView, self).get_context_data(*args, **kwargs)
        ctx.update(kwargs)

        # Don't pass request as we don't want to trigger validation of BOTH
        # forms.
        if 'login_form' not in kwargs:
            ctx['login_form'] = self.get_login_form()
        if 'registration_form' not in kwargs:
            ctx['registration_form'] = self.get_registration_form()
        return ctx

    def get_login_form(self, request=None):
        return self.login_form_class(**self.get_login_form_kwargs(request))

    def get_login_form_kwargs(self, request=None):
        kwargs = {}
        kwargs['host'] = self.request.get_host()
        kwargs['prefix'] = self.login_prefix
        kwargs['initial'] = {
            'redirect_url': self.request.GET.get(self.redirect_field_name, ''),
        }
        if request and request.method in ('POST', 'PUT'):
            kwargs.update({
                'data': request.POST,
                'files': request.FILES,
            })
        return kwargs

    def get_registration_form(self, request=None):
        return self.registration_form_class(
            **self.get_registration_form_kwargs(request))

    def get_registration_form_kwargs(self, request=None):
        kwargs = {}
        kwargs['host'] = self.request.get_host()
        kwargs['prefix'] = self.registration_prefix
        kwargs['initial'] = {
            'redirect_url': self.request.GET.get(self.redirect_field_name, ''),
        }
        if request and request.method in ('POST', 'PUT'):
            kwargs.update({
                'data': request.POST,
                'files': request.FILES,
            })
        return kwargs

    def post(self, request, *args, **kwargs):
        # Use the name of the submit button to determine which form to validate
        if u'login_submit' in request.POST:
            return self.validate_login_form()
        elif u'registration_submit' in request.POST:
            return self.validate_registration_form()
        return self.get(request)

    def validate_login_form(self):
        form = self.get_login_form(self.request)
        if form.is_valid():
            auth_login(self.request, form.get_user())
            return HttpResponseRedirect(form.cleaned_data['redirect_url'])

        ctx = self.get_context_data(login_form=form)
        return self.render_to_response(ctx)

    def validate_registration_form(self):
        form = self.get_registration_form(self.request)
        if form.is_valid():
            self.register_user(form)
            return HttpResponseRedirect(form.cleaned_data['redirect_url'])

        ctx = self.get_context_data(registration_form=form)
        return self.render_to_response(ctx)


class EmailHistoryView(ListView):
    """Customer email history"""
    context_object_name = "emails"
    template_name = 'customer/email_list.html'
    paginate_by = 20

    def get_queryset(self):
        """Return a customer's orders"""
        return Email._default_manager.filter(user=self.request.user)


class EmailDetailView(DetailView):
    """Customer order details"""
    template_name = "customer/email.html"
    context_object_name = 'email'

    def get_object(self, queryset=None):
        """Return an order object or 404"""
        return get_object_or_404(Email, user=self.request.user,
                                 id=self.kwargs['email_id'])


class OrderHistoryView(ListView):
    """
    Customer order history
    """
    context_object_name = "orders"
    template_name = 'customer/order_list.html'
    paginate_by = 20
    model = Order
    form_class = SearchByDateRangeForm

    def get(self, request, *args, **kwargs):
        if 'date_from' in request.GET:
            self.form = SearchByDateRangeForm(self.request.GET)
            if not self.form.is_valid():
                self.object_list = self.get_queryset()
                ctx = self.get_context_data(object_list=self.object_list)
                return self.render_to_response(ctx)
        else:
            self.form = SearchByDateRangeForm()
        return super(OrderHistoryView, self).get(request, *args, **kwargs)

    def get_queryset(self):
        qs = self.model._default_manager.filter(user=self.request.user)
        if self.form.is_bound and self.form.is_valid():
            qs = qs.filter(**self.form.get_filters())
        return qs

    def get_context_data(self, *args, **kwargs):
        ctx = super(OrderHistoryView, self).get_context_data(*args, **kwargs)
        ctx['form'] = self.form
        return ctx


class OrderDetailView(DetailView, PostActionMixin):
    """Customer order details"""
    model = Order

    def get_template_names(self):
        return ["customer/order.html"]

    def get_object(self, queryset=None):
        return get_object_or_404(self.model, user=self.request.user,
                                 number=self.kwargs['order_number'])

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
            is_available, reason = line.is_available_to_reorder(basket,
                self.request.strategy)
            if is_available:
                lines_to_add.append(line)
            else:
                warnings.append(reason)

        # Check whether the number of items in the basket won't exceed the
        # maximum.
        total_quantity = sum([line.quantity for line in lines_to_add])
        is_quantity_allowed, reason = basket.is_quantity_allowed(
            total_quantity)
        if not is_quantity_allowed:
            messages.warning(self.request, reason)
            self.response = HttpResponseRedirect(
                reverse('customer:order-list'))
            return

        # Add any warnings
        for warning in warnings:
            messages.warning(self.request, warning)

        for line in lines_to_add:
            options = []
            for attribute in line.attributes.all():
                if attribute.option:
                    options.append({
                        'option': attribute.option,
                        'value': attribute.value})
            basket.add_product(line.product, line.quantity, options)

        if len(lines_to_add) > 0:
            self.response = HttpResponseRedirect(reverse('basket:summary'))
            messages.info(
                self.request,
                _("All available lines from order %(number)s "
                  "have been added to your basket") % {'number': order.number})
        else:
            self.response = HttpResponseRedirect(
                reverse('customer:order-list'))
            messages.warning(
                self.request,
                _("It is not possible to re-order order %(number)s "
                  "as none of its lines are available to purchase") %
                {'number': order.number})


class OrderLineView(DetailView, PostActionMixin):
    """Customer order line"""

    def get_object(self, queryset=None):
        """Return an order object or 404"""
        order = get_object_or_404(Order, user=self.request.user,
                                  number=self.kwargs['order_number'])
        return order.lines.get(id=self.kwargs['line_id'])

    def do_reorder(self, line):
        self.response = HttpResponseRedirect(reverse('customer:order',
                                    args=(int(self.kwargs['order_number']),)))
        basket = self.request.basket

        line_available_to_reorder, reason = line.is_available_to_reorder(basket,
            self.request.user)

        if not line_available_to_reorder:
            messages.warning(self.request, reason)
            return

        # We need to pass response to the get_or_create... method
        # as a new basket might need to be created
        self.response = HttpResponseRedirect(reverse('basket:summary'))

        # Convert line attributes into basket options
        options = []
        for attribute in line.attributes.all():
            if attribute.option:
                options.append({'option': attribute.option, 'value': attribute.value})
        basket.add_product(line.product, line.quantity, options)

        if line.quantity > 1:
            msg = _("%(qty)d copies of '%(product)s' have been added to your basket") % {
                'qty': line.quantity, 'product': line.product}
        else:
            msg = _("'%s' has been added to your basket") % line.product

        messages.info(self.request, msg)


# ------------
# Address book
# ------------


class AddressListView(ListView):
    """Customer address book"""
    context_object_name = "addresses"
    template_name = 'customer/address_list.html'
    paginate_by = 40

    def get_queryset(self):
        """Return a customer's addresses"""
        return UserAddress._default_manager.filter(user=self.request.user)


class AddressCreateView(CreateView):
    form_class = UserAddressForm
    mode = UserAddress
    template_name = 'customer/address_form.html'

    def get_form_kwargs(self):
        kwargs = super(AddressCreateView, self).get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def get_context_data(self, **kwargs):
        ctx = super(AddressCreateView, self).get_context_data(**kwargs)
        ctx['title'] = _('Add a new address')
        return ctx

    def get_success_url(self):
        messages.success(self.request, _("Address saved"))
        return reverse('customer:address-list')


class AddressUpdateView(UpdateView):
    form_class = UserAddressForm
    model = UserAddress
    template_name = 'customer/address_form.html'

    def get_form_kwargs(self):
        kwargs = super(AddressUpdateView, self).get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def get_context_data(self, **kwargs):
        ctx = super(AddressUpdateView, self).get_context_data(**kwargs)
        ctx['title'] = _('Edit address')
        return ctx

    def get_queryset(self):
        return self.request.user.addresses.all()

    def get_success_url(self):
        messages.success(self.request, _("Address saved"))
        return reverse('customer:address-list')


class AddressDeleteView(DeleteView):
    model = UserAddress
    template_name = "customer/address_delete.html"

    def get_queryset(self):
        return UserAddress._default_manager.filter(user=self.request.user)

    def get_success_url(self):
        return reverse('customer:address-list')


# ------------
# Order status
# ------------


class AnonymousOrderDetailView(DetailView):
    model = Order
    template_name = "customer/anon_order.html"

    def get_object(self, queryset=None):
        # Check URL hash matches that for order to prevent spoof attacks
        order = get_object_or_404(self.model, user=None,
                                  number=self.kwargs['order_number'])
        if self.kwargs['hash'] != order.verification_hash():
            raise Http404()
        return order


class ChangePasswordView(FormView):
    form_class = PasswordChangeForm
    template_name = 'customer/change_password_form.html'
    communication_type_code = 'PASSWORD_CHANGED'

    def get_form_kwargs(self):
        kwargs = super(ChangePasswordView, self).get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        form.save()
        messages.success(self.request, _("Password updated"))

        ctx = {
            'user': self.request.user,
            'site': get_current_site(self.request),
            'reset_url': get_password_reset_url(self.request.user),
        }
        msgs = CommunicationEventType.objects.get_and_render(
            code=self.communication_type_code, context=ctx)
        Dispatcher().dispatch_user_messages(self.request.user, msgs)

        return HttpResponseRedirect(self.get_success_url())

    def get_success_url(self):
        return reverse('customer:summary')
