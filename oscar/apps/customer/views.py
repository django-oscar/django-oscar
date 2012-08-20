import urlparse

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
from oscar.core.loading import get_class, get_profile_class, get_classes
Dispatcher = get_class('customer.utils', 'Dispatcher')
EmailAuthenticationForm, EmailUserCreationForm, SearchByDateRangeForm = get_classes(
    'customer.forms', ['EmailAuthenticationForm', 'EmailUserCreationForm',
                       'SearchByDateRangeForm'])
ProfileForm = get_class('customer.forms', 'ProfileForm')
UserAddressForm = get_class('address.forms', 'UserAddressForm')
Order = get_model('order', 'Order')
Line = get_model('basket', 'Line')
Basket = get_model('basket', 'Basket')
UserAddress = get_model('address', 'UserAddress')
Email = get_model('customer', 'email')
UserAddress = get_model('address', 'UserAddress')
CommunicationEventType = get_model('customer', 'communicationeventtype')


class LogoutView(RedirectView):
    url = '/'

    def get(self, request, *args, **kwargs):
        auth_logout(request)
        response = super(LogoutView, self).get(request, *args, **kwargs)

        for cookie in settings.OSCAR_COOKIES_DELETE_ON_LOGOUT:
            response.delete_cookie(cookie)

        return response


class ProfileUpdateView(FormView):
    form_class = ProfileForm
    template_name = 'customer/profile-form.html'

    def get_form_kwargs(self):
        kwargs = super(ProfileUpdateView, self).get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        form.save()
        messages.success(self.request, "Profile updated")
        return HttpResponseRedirect(self.get_success_url())

    def get_success_url(self):
        return reverse('customer:summary')


class AccountSummaryView(ListView):
    context_object_name = "orders"
    template_name = 'customer/profile.html'
    paginate_by = 20
    model = Order

    def get_queryset(self):
        return self.model._default_manager.filter(user=self.request.user)[0:5]

    def get_context_data(self, **kwargs):
        ctx = super(AccountSummaryView, self).get_context_data(**kwargs)
        ctx['addressbook_size'] = self.request.user.addresses.all().count()
        ctx['default_shipping_address'] = self.get_default_shipping_address(self.request.user)
        ctx['default_billing_address'] = self.get_default_billing_address(self.request.user)
        ctx['emails'] = Email.objects.filter(user=self.request.user)
        self.add_profile_fields(ctx)
        return ctx

    def add_profile_fields(self, ctx):
        if not hasattr(settings, 'AUTH_PROFILE_MODULE'):
            return
        try:
            profile = self.request.user.get_profile()
        except ObjectDoesNotExist:
            profile = get_profile_class()()

        field_data = []
        for field_name in profile._meta.get_all_field_names():
            if field_name in ('user', 'id'):
                continue
            field = profile._meta.get_field(field_name)
            if field.choices:
                value = getattr(profile, 'get_%s_display' % field_name)()
            else:
                value = getattr(profile, field_name)
            field_data.append({
                'name': getattr(field, 'verbose_name'),
                'value': value,
            })
        ctx['profile_fields'] = field_data
        ctx['profile'] = profile

    def get_default_billing_address(self, user):
        return self.get_user_address(user, is_default_for_billing=True)

    def get_default_shipping_address(self, user):
        return self.get_user_address(user, is_default_for_shipping=True)

    def get_user_address(self, user, **filters):
        try:
            return user.addresses.get(**filters)
        except UserAddress.DoesNotExist:
            return None


class AccountRegistrationView(TemplateView):
    template_name = 'customer/registration.html'
    redirect_field_name = 'next'
    registration_prefix = 'registration'
    communication_type_code = 'REGISTRATION'

    def get_logged_in_redirect(self):
        return reverse('customer:summary')

    def check_redirect(self, context):
        redirect_to = context.get(self.redirect_field_name)
        if not redirect_to:
            return settings.LOGIN_REDIRECT_URL

        netloc = urlparse.urlparse(redirect_to)[1]
        if netloc and netloc != self.request.get_host():
            return settings.LOGIN_REDIRECT_URL

        return redirect_to

    def get_context_data(self, *args, **kwargs):
        context = super(AccountRegistrationView, self).get_context_data(*args, **kwargs)
        redirect_to = self.request.REQUEST.get(self.redirect_field_name, '')
        context[self.redirect_field_name] = redirect_to
        context['registration_form'] = EmailUserCreationForm(
            prefix=self.registration_prefix
        )
        return context

    def send_registration_email(self, user):
        code = self.communication_type_code
        ctx = {'user': user,
               'site': get_current_site(self.request)}
        try:
            event_type = CommunicationEventType.objects.get(code=code)
        except CommunicationEventType.DoesNotExist:
            # No event in database, attempt to find templates for this type
            messages = CommunicationEventType.objects.get_and_render(code, ctx)
        else:
            # Create order event
            messages = event_type.get_messages(ctx)

        if messages and messages['body']:
            dispatcher = Dispatcher()
            dispatcher.dispatch_user_messages(user, messages)

    def get(self, request, *args, **kwargs):
        context = self.get_context_data(*args, **kwargs)

        if request.user.is_authenticated():
            return HttpResponseRedirect(self.get_logged_in_redirect())

        self.request.session.set_test_cookie()
        return self.render_to_response(context)

    def post(self, request, *args, **kwargs):
        context = self.get_context_data(*args, **kwargs)
        redirect_to = self.check_redirect(context)

        registration_form = EmailUserCreationForm(
            prefix=self.registration_prefix,
            data=request.POST
        )
        context['registration_form'] = registration_form

        if registration_form.is_valid():
            self._register_user(registration_form)
            return HttpResponseRedirect(redirect_to)

        self.request.session.set_test_cookie()
        return self.render_to_response(context)

    def _register_user(self, form):
        """
        Register a new user from the data in *form*. If
        ``OSCAR_SEND_REGISTRATION_EMAIL`` is set to ``True`` a
        registration email will be send to the provided email address.
        A new user account is created and the user is then logged
        in.
        """
        user = form.save()

        if getattr(settings, 'OSCAR_SEND_REGISTRATION_EMAIL', True):
            self.send_registration_email(user)

        user = authenticate(
            username=user.email,
            password=form.cleaned_data['password1']
        )
        auth_login(self.request, user)
        if self.request.session.test_cookie_worked():
            self.request.session.delete_test_cookie()


class AccountAuthView(AccountRegistrationView):
    template_name = 'customer/login_registration.html'
    login_prefix = 'login'

    def get_context_data(self, *args, **kwargs):
        context = super(AccountAuthView, self).get_context_data(*args, **kwargs)
        redirect_to = self.request.REQUEST.get(self.redirect_field_name, '')
        context[self.redirect_field_name] = redirect_to
        context['login_form'] = EmailAuthenticationForm(prefix=self.login_prefix)
        context['registration_form'] = EmailUserCreationForm(prefix=self.registration_prefix)
        return context

    def post(self, request, *args, **kwargs):
        context = self.get_context_data(*args, **kwargs)
        redirect_to = self.check_redirect(context)

        if u'login_submit' in self.request.POST:
            login_form = EmailAuthenticationForm(
                prefix=self.login_prefix,
                data=request.POST
            )
            if login_form.is_valid():
                auth_login(request, login_form.get_user())
                if request.session.test_cookie_worked():
                    request.session.delete_test_cookie()
                return HttpResponseRedirect(redirect_to)
            context['login_form'] = login_form

        if u'registration_submit' in self.request.POST:
            registration_form = EmailUserCreationForm(
                prefix=self.registration_prefix,
                data=request.POST
            )
            context['registration_form'] = registration_form

            if registration_form.is_valid():
                self._register_user(registration_form)
                return HttpResponseRedirect(redirect_to)

        self.request.session.set_test_cookie()
        return self.render_to_response(context)


class EmailHistoryView(ListView):
    """Customer email history"""
    context_object_name = "emails"
    template_name = 'customer/email-history.html'
    paginate_by = 20

    def get_queryset(self):
        """Return a customer's orders"""
        return Email._default_manager.filter(user=self.request.user)


class EmailDetailView(DetailView):
    """Customer order details"""
    template_name = "customer/email.html"
    context_object_name = 'email'

    def get_object(self):
        """Return an order object or 404"""
        return get_object_or_404(Email, user=self.request.user, id=self.kwargs['email_id'])


class OrderHistoryView(ListView):
    """
    Customer order history
    """
    context_object_name = "orders"
    template_name = 'customer/order-history.html'
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

    def get_object(self):
        return get_object_or_404(self.model, user=self.request.user, number=self.kwargs['order_number'])

    def do_reorder(self, order):
        """
        'Re-order' a previous order.

        This puts the contents of the previous order into your basket
        """
        basket = self.request.basket

        # Convert line attributes into basket options
        lines_added = []
        warnings = []
        # Collect lines to be added to the basket and the warnings
        for line in order.lines.all():
            if not line.product:
                warnings.append(_("'%s' unavailable for re-order") % line.title)
                continue

            try:
                basket_line = basket.lines.get(product=line.product)
            except Line.DoesNotExist:
                desired_qty = line.quantity
            else:
                desired_qty = basket_line.quantity + line.quantity

            is_available, reason = line.product.is_purchase_permitted(
                                                        user=self.request.user,
                                                        quantity=desired_qty)
            if not is_available:
                warnings.append(reason)
                continue

            lines_added.append(line)

        # Check whether the number of items in the basket won't exceed the maximum
        total_quantity = sum([line.quantity for line in lines_added])
        is_quantity_allowed, reason = basket.is_quantity_allowed(total_quantity)

        self.response = HttpResponseRedirect(reverse('customer:order-list'))

        if not is_quantity_allowed:
            messages.warning(self.request, reason)
            return
        else:
            # Add items to the basket, display warnings
            for warning in warnings:
                messages.warning(self.request, warning)

            for line in lines_added:
                options = []
                for attribute in line.attributes.all():
                    if attribute.option:
                        options.append({'option': attribute.option, 'value': attribute.value})
                basket.add_product(line.product, line.quantity, options)

        if len(lines_added) > 0:
            self.response = HttpResponseRedirect(reverse('basket:summary'))
            messages.info(self.request,
                          _("All available lines from order %s "
                            "have been added to your basket") % order.number)


class OrderLineView(DetailView, PostActionMixin):
    """Customer order line"""

    def get_object(self):
        """Return an order object or 404"""
        order = get_object_or_404(Order, user=self.request.user, number=self.kwargs['order_number'])
        return order.lines.get(id=self.kwargs['line_id'])

    def do_reorder(self, line):
        self.response = HttpResponseRedirect(reverse('customer:order',
                                    args=(int(self.kwargs['order_number']),)))
        basket = self.request.basket

        # Check whether basket items quantity won't exceed the maximum
        is_quantity_allowed, reason = basket.is_quantity_allowed(line.quantity)
        if not is_quantity_allowed:
            messages.warning(self.request, reason)
            return

        if not line.product:
            messages.info(self.request, _("This product is no longer available for re-order"))
            return

        try:
            basket_line = basket.lines.get(product=line.product)
        except Line.DoesNotExist:
            desired_qty = line.quantity
        else:
            desired_qty = basket_line.quantity + line.quantity

        is_available, reason = line.product.is_purchase_permitted(
                                                    user=self.request.user,
                                                    quantity=desired_qty)

        if not is_available:
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


class AddressListView(ListView):
    """Customer address book"""
    context_object_name = "addresses"
    template_name = 'customer/address-book.html'
    paginate_by = 40

    def get_queryset(self):
        """Return a customer's addresses"""
        return UserAddress._default_manager.filter(user=self.request.user)


class AddressCreateView(CreateView):
    form_class = UserAddressForm
    mode = UserAddress
    template_name = 'customer/address-form.html'

    def get_context_data(self, **kwargs):
        ctx =  super(AddressCreateView, self).get_context_data(**kwargs)
        ctx['title'] = _('Add a new address')
        return ctx

    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.user = self.request.user
        self.object.save()
        return HttpResponseRedirect(self.get_success_url())

    def get_success_url(self):
        messages.success(self.request, _("Address saved"))
        return reverse('customer:address-list')


class AddressUpdateView(UpdateView):
    form_class = UserAddressForm
    model = UserAddress
    template_name = 'customer/address-form.html'

    def get_context_data(self, **kwargs):
        ctx =  super(AddressUpdateView, self).get_context_data(**kwargs)
        ctx['title'] = _('Edit address')
        return ctx

    def get_queryset(self):
        return UserAddress._default_manager.filter(user=self.request.user)

    def get_success_url(self):
        messages.success(self.request, _("Address saved"))
        return reverse('customer:address-detail', kwargs={'pk': self.get_object().pk })


class AddressDeleteView(DeleteView):
    model = UserAddress

    def get_queryset(self):
        """Return a customer's addresses"""
        return UserAddress._default_manager.filter(user=self.request.user)

    def get_success_url(self):
        return reverse('customer:address-list')

    def get_template_names(self):
        return ["customer/address-delete.html"]


class AnonymousOrderDetailView(DetailView):

    model = Order

    def get_template_names(self):
        return ["customer/anon-order.html"]

    def get_object(self):
        order = get_object_or_404(self.model, user=None, number=self.kwargs['order_number'])
        if self.kwargs['hash'] != order.verification_hash():
            raise Http404()

        return order


class ChangePasswordView(FormView):
    form_class = PasswordChangeForm
    template_name = 'customer/change-password.html'

    def get_form_kwargs(self):
        kwargs = super(ChangePasswordView, self).get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        form.save()
        messages.success(self.request, _("Password updated"))
        return HttpResponseRedirect(self.get_success_url())

    def get_success_url(self):
        return reverse('customer:summary')
