import urlparse

from django.shortcuts import get_object_or_404
from django.views.generic import (TemplateView, ListView, DetailView,
                                  CreateView, UpdateView, DeleteView,
                                  FormView, RedirectView)
from django.core.urlresolvers import reverse, reverse_lazy
from django.core.exceptions import ObjectDoesNotExist
from django.http import HttpResponseRedirect, Http404
from django.contrib import messages
from django.utils.translation import ugettext_lazy as _
from django.contrib.auth import (authenticate, login as auth_login,
                                 logout as auth_logout)
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.sites.models import get_current_site
from django.contrib.auth.models import User
from django.conf import settings
from django.db.models import get_model

from oscar.views.generic import PostActionMixin
from oscar.apps.customer.utils import get_password_reset_url
from oscar.core.loading import get_class, get_profile_class, get_classes
from .mixins import PageTitleMixin

Dispatcher = get_class('customer.utils', 'Dispatcher')
EmailAuthenticationForm, EmailUserCreationForm, OrderSearchForm = get_classes(
    'customer.forms', ['EmailAuthenticationForm', 'EmailUserCreationForm',
                       'OrderSearchForm'])
ProfileForm = get_class('customer.forms', 'ProfileForm')
UserAddressForm = get_class('address.forms', 'UserAddressForm')
user_registered = get_class('customer.signals', 'user_registered')
Order = get_model('order', 'Order')
Line = get_model('basket', 'Line')
Basket = get_model('basket', 'Basket')
UserAddress = get_model('address', 'UserAddress')
Email = get_model('customer', 'email')
UserAddress = get_model('address', 'UserAddress')
CommunicationEventType = get_model('customer', 'communicationeventtype')
ProductAlert = get_model('customer', 'ProductAlert')


class LogoutView(RedirectView):
    url = '/'
    permanent = False

    def get(self, request, *args, **kwargs):
        auth_logout(request)
        response = super(LogoutView, self).get(request, *args, **kwargs)

        for cookie in settings.OSCAR_COOKIES_DELETE_ON_LOGOUT:
            response.delete_cookie(cookie)

        return response


class AccountSummaryView(RedirectView):
    url = reverse_lazy(settings.OSCAR_ACCOUNTS_REDIRECT_URL)


class ProfileView(PageTitleMixin, TemplateView):
    template_name = 'customer/profile/profile.html'
    page_title = _('Profile')
    active_tab = 'profile'

    def get_context_data(self, **kwargs):
        ctx = super(ProfileView, self).get_context_data(**kwargs)
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
        return ctx


class ProfileUpdateView(PageTitleMixin, FormView):
    form_class = ProfileForm
    template_name = 'customer/profile/profile_form.html'
    communication_type_code = 'EMAIL_CHANGED'
    page_title = _('Edit Profile')
    active_tab = 'profile'

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
        return reverse('customer:profile-view')


class ChangePasswordView(PageTitleMixin, FormView):
    form_class = PasswordChangeForm
    template_name = 'customer/profile/change_password_form.html'
    communication_type_code = 'PASSWORD_CHANGED'
    page_title = _('Change Password')
    active_tab = 'profile'

    def get_form_kwargs(self):
        kwargs = super(ChangePasswordView, self).get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        form.save()
        messages.success(self.request, _("Password updated"))

        ctx = {
            'site': get_current_site(self.request),
            'reset_url': get_password_reset_url(self.request.user),
            }
        msgs = CommunicationEventType.objects.get_and_render(
            code=self.communication_type_code, context=ctx)
        Dispatcher().dispatch_user_messages(self.request.user, msgs)

        return HttpResponseRedirect(self.get_success_url())

    def get_success_url(self):
        return reverse('customer:profile-view')


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
        messages = CommunicationEventType.objects.get_and_render(
            code, ctx)
        if messages and messages['body']:
            Dispatcher().dispatch_user_messages(user, messages)

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
        A new user account is created and the user is then logged in.
        """
        user = form.save()

        if getattr(settings, 'OSCAR_SEND_REGISTRATION_EMAIL', True):
            self.send_registration_email(user)

        user_registered.send_robust(sender=self, user=user)

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


class EmailHistoryView(PageTitleMixin, ListView):
    """Customer email history"""
    context_object_name = "emails"
    template_name = 'customer/email/email_list.html'
    paginate_by = 20
    page_title = _('Email History')
    active_tab = 'emails'

    def get_queryset(self):
        """Return a customer's emails"""
        return Email._default_manager.filter(user=self.request.user)


class EmailDetailView(PageTitleMixin, DetailView):
    """Customer email"""
    template_name = "customer/email/email.html"
    context_object_name = 'email'
    active_tab = 'emails'

    def get_object(self, queryset=None):
        """Return an order object or 404"""
        return get_object_or_404(Email, user=self.request.user,
                                 id=self.kwargs['email_id'])

    def get_page_title(self):
        """Append email subject to page title"""
        return u'%s: %s' % (_('Email'), self.object.subject)


class OrderHistoryView(PageTitleMixin, ListView):
    """
    Customer order history
    """
    context_object_name = "orders"
    template_name = 'customer/order/order_list.html'
    paginate_by = 20
    model = Order
    form_class = OrderSearchForm
    page_title = _('Order History')
    active_tab = 'orders'

    def get(self, request, *args, **kwargs):
        if 'date_from' in request.GET:
            self.form = OrderSearchForm(self.request.GET)
            if not self.form.is_valid():
                self.object_list = self.get_queryset()
                ctx = self.get_context_data(object_list=self.object_list)
                return self.render_to_response(ctx)
            data = self.form.cleaned_data

            # If the user has just entered an order number, try and look it up
            # and redirect immediately to the order detail page.
            if data['order_number'] and not (data['date_to'] or
                                             data['date_from']):
                try:
                    order = Order.objects.get(
                        number=data['order_number'], user=self.request.user)
                except Order.DoesNotExist:
                    pass
                else:
                    return HttpResponseRedirect(
                        reverse('customer:order',
                                kwargs={'order_number': order.number}))
        else:
            self.form = OrderSearchForm()
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


class OrderDetailView(PageTitleMixin, DetailView, PostActionMixin):
    """Customer order details"""
    model = Order
    active_tab = 'orders'

    def get_template_names(self):
        return ["customer/order/order.html"]

    def get_page_title(self):
        """ Order number as page title """
        return u'%s #%s' % (_('Order'), self.object.number)

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
                self.request.user)
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


class AddressListView(PageTitleMixin, ListView):
    """Customer address book"""
    context_object_name = "addresses"
    template_name = 'customer/address/address_list.html'
    paginate_by = 40
    active_tab = 'addresses'
    page_title = _('Address Book')

    def get_queryset(self):
        """Return customer's addresses"""
        return UserAddress._default_manager.filter(user=self.request.user)


class AddressCreateView(PageTitleMixin, CreateView):
    form_class = UserAddressForm
    model = UserAddress
    template_name = 'customer/address/address_form.html'
    active_tab = 'addresses'
    page_title = _('Add a new address')

    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.user = self.request.user
        self.object.save()
        return HttpResponseRedirect(self.get_success_url())

    def get_success_url(self):
        messages.success(self.request,
                         _("Address '%s' created") % self.object.summary)
        return reverse('customer:address-list')


class AddressUpdateView(PageTitleMixin, UpdateView):
    form_class = UserAddressForm
    model = UserAddress
    template_name = 'customer/address/address_form.html'
    active_tab = 'addresses'
    page_title = _('Edit address')

    def get_queryset(self):
        return UserAddress._default_manager.filter(user=self.request.user)

    def get_success_url(self):
        messages.success(self.request,
                         _("Address '%s' updated") % self.object.summary)
        return reverse('customer:address-detail', kwargs={'pk': self.get_object().pk })


class AddressDeleteView(PageTitleMixin, DeleteView):
    model = UserAddress
    template_name = "customer/address/address_delete.html"
    page_title = _('Delete address?')
    active_tab = 'addresses'
    context_object_name = 'address'

    def get_queryset(self):
        return UserAddress._default_manager.filter(user=self.request.user)

    def get_success_url(self):
        messages.success(self.request,
                         _("Address '%s' deleted") % self.object.summary)
        return reverse('customer:address-list')


class AddressChangeStatusView(RedirectView):
    """
    Sets an address as default_for_(billing|shipping)
    """
    url = reverse_lazy('customer:address-list')

    def get(self, request, pk=None, action=None, *args, **kwargs):
        address = get_object_or_404(UserAddress, user=self.request.user,
                                    pk=pk)
        setattr(address, 'is_%s' % action, True)
        address.save()
        return super(AddressChangeStatusView, self).get(request, *args, **kwargs)


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


