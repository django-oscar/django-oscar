from urlparse import urlparse
from django.contrib import messages
from django.core.urlresolvers import reverse, resolve
from django.db.models import get_model
from django.http import HttpResponseRedirect, Http404
from django.views.generic import FormView, View
from django.utils.translation import ugettext_lazy as _
from django.core.exceptions import ObjectDoesNotExist

from extra_views import ModelFormSetView
from oscar.apps.basket.signals import basket_addition, voucher_addition
from oscar.core.loading import get_class, get_classes
from oscar.views import generic


Applicator = get_class('offer.utils', 'Applicator')
BasketLineForm, AddToBasketForm, BasketVoucherForm, \
        SavedLineFormSet, SavedLineForm, ProductSelectionForm = get_classes(
            'basket.forms', ('BasketLineForm', 'AddToBasketForm',
                             'BasketVoucherForm', 'SavedLineFormSet',
                             'SavedLineForm', 'ProductSelectionForm'))
Repository = get_class('shipping.repository', ('Repository'))


def apply_messages(offers_before, request, default_msg=None):
    """
    Set flash messages triggered by changes to the basket
    """
    # Re-apply offers to see if any new ones are now available
    Applicator().apply(request, request.basket)
    offers_after = request.basket.get_discount_offers()

    # Look for changes in offers
    offers_lost = set(offers_before.keys()).difference(
        set(offers_after.keys()))
    offers_gained = set(offers_after.keys()).difference(
        set(offers_before.keys()))
    for offer_id in offers_lost:
        offer = offers_before[offer_id]
        messages.warning(
            request,
            _("Your basket no longer qualifies for the '%s' offer") % offer)
    for offer_id in offers_gained:
        offer = offers_after[offer_id]
        messages.success(
            request,
            _("Your basket now qualifies for the '%s' offer") % offer)
    if not offers_lost and not offers_gained:
        messages.info(request, default_msg)


class BasketView(generic.CountersMixin, ModelFormSetView):
    model = get_model('basket', 'Line')
    basket_model = get_model('basket', 'Basket')
    form_class = BasketLineForm
    extra = 0
    can_delete = True
    template_name = 'basket/basket.html'

    def get_queryset(self):
        return self.request.basket.all_lines()

    def get_shipping_methods(self, basket):
        return Repository().get_shipping_methods(
            self.request.user, self.request.basket)

    def get_default_shipping_method(self, basket):
        return Repository().get_default_shipping_method(
            self.request.user, self.request.basket)

    def get_basket_warnings(self, basket):
        """
        Return a list of warnings that apply to this basket
        """
        warnings = []
        for line in basket.all_lines():
            warning = line.get_warning()
            if warning:
                warnings.append(warning)
        return warnings

    def get_upsell_messages(self, basket):
        offers = Applicator().get_offers(self.request, basket)
        msgs = []
        for offer in offers:
            if offer.is_condition_partially_satisfied(basket):
                data = {
                    'message': offer.get_upsell_message(basket),
                    'offer': offer}
                msgs.append(data)
        return msgs

    def get_context_data(self, **kwargs):
        context = super(BasketView, self).get_context_data(**kwargs)
        context['voucher_form'] = BasketVoucherForm()

        # Shipping information is included to give an idea of the total order
        # cost.  It is also important for PayPal Express where the customer
        # gets redirected away from the basket page and needs to see what the
        # estimated order total is beforehand.
        method = self.get_default_shipping_method(self.request.basket)
        context['shipping_method'] = method
        context['shipping_methods'] = self.get_shipping_methods(
            self.request.basket)

        context['order_total_incl_tax'] = (
            self.request.basket.total_incl_tax +
            method.basket_charge_incl_tax())
        context['basket_warnings'] = self.get_basket_warnings(
            self.request.basket)
        context['upsell_messages'] = self.get_upsell_messages(
            self.request.basket)

        if self.request.user.is_authenticated():
            try:
                saved_basket = self.basket_model.saved.get(
                    owner=self.request.user)
            except self.basket_model.DoesNotExist:
                pass
            else:
                if not saved_basket.is_empty:
                    saved_queryset = saved_basket.all_lines().select_related(
                        'product', 'product__stockrecord')
                    formset = SavedLineFormSet(user=self.request.user,
                                               basket=self.request.basket,
                                               queryset=saved_queryset,
                                               prefix='saved')
                    context['saved_formset'] = formset
        return context

    def get_success_url(self):
        return self.request.META.get('HTTP_REFERER', reverse('basket:summary'))

    def formset_valid(self, formset):
        # Store offers before any changes are made so we can inform the user of
        # any changes
        offers_before = self.request.basket.get_discount_offers()
        save_for_later = False
        for form in formset:
            if (hasattr(form, 'cleaned_data') and
                form.cleaned_data['save_for_later']):
                line = form.instance
                if self.request.user.is_authenticated():
                    self.move_line_to_saved_basket(line)
                    messages.info(
                        self.request,
                        _(u"'%(title)s' has been saved for later") % {
                            'title': line.product})
                    save_for_later = True
                else:
                    messages.error(
                        self.request,
                        _("You can't save an item for later if you're not logged in!"))
                    return HttpResponseRedirect(self.get_success_url())

        if save_for_later:
            # No need to call super if we're moving lines to the saved basket
            response = HttpResponseRedirect(self.get_success_url())
        else:
            # Save changes to basket as per normal
            response = super(BasketView, self).formset_valid(formset)

        apply_messages(offers_before, self.request,
                       default_msg=_("Basket updated"))

        return response

    def move_line_to_saved_basket(self, line):
        saved_basket, _ = get_model('basket', 'basket').saved.get_or_create(
            owner=self.request.user)
        saved_basket.merge_line(line)

    def formset_invalid(self, formset):
        errors = []
        for error_dict in formset.errors:
            errors += [error_list.as_text()
                       for error_list in error_dict.values()]
        msg = _("Your basket couldn't be updated because:\n%s") % (
            "\n".join(errors),)
        messages.warning(self.request, msg)
        return super(BasketView, self).formset_invalid(formset)


class BasketAddView(generic.CountersMixin, FormView):
    """
    Handles the add-to-basket operation, shouldn't be accessed via
    GET because there's nothing sensible to render.
    """
    form_class = AddToBasketForm
    product_select_form_class = ProductSelectionForm
    product_model = get_model('catalogue', 'product')
    add_signal = basket_addition

    def get(self, request, *args, **kwargs):
        return HttpResponseRedirect(reverse('basket:summary'))

    def get_form_kwargs(self):
        kwargs = super(BasketAddView, self).get_form_kwargs()
        product_select_form = self.product_select_form_class(self.request.POST)

        if product_select_form.is_valid():
            kwargs['instance'] = product_select_form.cleaned_data['product_id']
        else:
            kwargs['instance'] = None
        kwargs['user'] = self.request.user
        kwargs['basket'] = self.request.basket
        return kwargs

    def get_success_url(self):
        url = None
        if self.request.POST.get('next'):
            url = self.request.POST.get('next')
        elif 'HTTP_REFERER' in self.request.META:
            url = self.request.META['HTTP_REFERER']
        if url:
            # We only allow internal URLs so we see if the url resolves
            try:
                resolve(urlparse(url).path)
            except Http404:
                url = None
        if url is None:
            url = reverse('basket:summary')
        return url

    def form_valid(self, form):
        offers_before = self.request.basket.get_discount_offers()
        self.request.basket.add_product(
            form.instance, form.cleaned_data['quantity'],
            form.cleaned_options())
        messages.success(self.request, self.get_success_message(form))

        # Check for additional offer messages
        apply_messages(offers_before, self.request)

        # Send signal for basket addition
        self.add_signal.send(
            sender=self, product=form.instance, user=self.request.user)

        return super(BasketAddView, self).form_valid(form)

    def get_success_message(self, form):
        qty = form.cleaned_data['quantity']
        title = form.instance.get_title()
        if qty == 1:
            return _("'%(title)s' has been added to your basket") % {
                'title': title}
        else:
            return _(
                "'%(title)s' (quantity %(quantity)d) has been added to your"
                "basket") % {'title': title, 'quantity': qty}

    def form_invalid(self, form):
        msgs = []
        for error in form.errors.values():
            msgs.append(error.as_text())
        messages.error(self.request, ",".join(msgs))
        return HttpResponseRedirect(
            self.request.META.get('HTTP_REFERER', reverse('basket:summary')))


class VoucherAddView(generic.CountersMixin, FormView):
    form_class = BasketVoucherForm
    voucher_model = get_model('voucher', 'voucher')
    add_signal = voucher_addition

    def get(self, request, *args, **kwargs):
        return HttpResponseRedirect(reverse('basket:summary'))

    def apply_voucher_to_basket(self, voucher):
        if not voucher.is_active():
            messages.error(
                self.request,
                _("The '%(code)s' voucher has expired") % {
                    'code': voucher.code})
            return

        is_available, message = voucher.is_available_to_user(self.request.user)
        if not is_available:
            messages.error(self.request, message)
            return

        self.request.basket.vouchers.add(voucher)

        # Raise signal
        self.add_signal.send(sender=self,
                             basket=self.request.basket,
                             voucher=voucher)

        # Recalculate discounts to see if the voucher gives any
        Applicator().apply(self.request, self.request.basket)
        discounts_after = self.request.basket.get_discounts()

        # Look for discounts from this new voucher
        found_discount = False
        for discount in discounts_after:
            if discount['voucher'] and discount['voucher'] == voucher:
                found_discount = True
                break
        if not found_discount:
            messages.warning(
                self.request,
                _("Your basket does not qualify for a voucher discount"))
            self.request.basket.vouchers.remove(voucher)
        else:
            messages.info(
                self.request,
                _("Voucher '%(code)s' added to basket") % {
                    'code': voucher.code})

    def form_valid(self, form):
        code = form.cleaned_data['code']
        if not self.request.basket.id:
            return HttpResponseRedirect(
                self.request.META.get('HTTP_REFERER',
                                      reverse('basket:summary')))
        if self.request.basket.contains_voucher(code):
            messages.error(
                self.request,
                _("You have already added the '%(code)s' voucher to "
                  "your basket") % {'code': code})
        else:
            try:
                voucher = self.voucher_model._default_manager.get(code=code)
            except self.voucher_model.DoesNotExist:
                messages.error(
                    self.request,
                    _("No voucher found with code '%(code)s'") % {
                        'code': code})
            else:
                self.apply_voucher_to_basket(voucher)
        return HttpResponseRedirect(
            self.request.META.get('HTTP_REFERER', reverse('basket:summary')))

    def form_invalid(self, form):
        messages.error(self.request, _("Please enter a voucher code"))
        return HttpResponseRedirect(reverse('basket:summary') + '#voucher')


class VoucherRemoveView(generic.CountersMixin, View):
    voucher_model = get_model('voucher', 'voucher')

    def get(self, request, *args, **kwargs):
        return HttpResponseRedirect(reverse('basket:summary'))

    def post(self, request, *args, **kwargs):
        voucher_id = int(kwargs.pop('pk'))
        if not request.basket.id:
            # Hacking attempt - the basket must be saved for it to have
            # a voucher in it.
            return HttpResponseRedirect(reverse('basket:summary'))
        try:
            voucher = request.basket.vouchers.get(id=voucher_id)
        except ObjectDoesNotExist:
            messages.error(
                request, _("No voucher found with id '%d'") % voucher_id)
        else:
            request.basket.vouchers.remove(voucher)
            request.basket.save()
            messages.info(
                request, _("Voucher '%s' removed from basket") % voucher.code)
        return HttpResponseRedirect(reverse('basket:summary'))


class SavedView(generic.CountersMixin, ModelFormSetView):
    model = get_model('basket', 'line')
    basket_model = get_model('basket', 'basket')
    formset_class = SavedLineFormSet
    form_class = SavedLineForm
    extra = 0
    can_delete = True

    def get(self, request, *args, **kwargs):
        return HttpResponseRedirect(reverse('basket:summary'))

    def get_queryset(self):
        try:
            saved_basket = self.basket_model.saved.get(owner=self.request.user)
            return saved_basket.all_lines().select_related(
                'product', 'product__stockrecord')
        except self.basket_model.DoesNotExist:
            return []

    def get_success_url(self):
        return self.request.META.get('HTTP_REFERER', reverse('basket:summary'))

    def get_formset_kwargs(self):
        kwargs = super(SavedView, self).get_formset_kwargs()
        kwargs['prefix'] = 'saved'
        kwargs['basket'] = self.request.basket
        kwargs['user'] = self.request.user
        return kwargs

    def formset_valid(self, formset):
        offers_before = self.request.basket.get_discount_offers()

        is_move = False
        for form in formset:
            if form.cleaned_data['move_to_basket']:
                is_move = True
                msg = _("'%(product)s' has been moved back to your basket") % {
                    'product': form.instance.product}
                messages.info(self.request, msg)
                real_basket = self.request.basket
                real_basket.merge_line(form.instance)

        if is_move:
            apply_messages(offers_before, self.request)
            return HttpResponseRedirect(self.get_success_url())

        return super(SavedView, self).formset_valid(formset)

    def formset_invalid(self, formset):
        messages.error(
            self.request,
            '\n'.join(
                error for ed in formset.errors for el
                in ed.values() for error in el))
        return HttpResponseRedirect(
            self.request.META.get('HTTP_REFERER', reverse('basket:summary')))
