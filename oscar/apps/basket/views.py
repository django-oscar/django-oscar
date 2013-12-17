from urlparse import urlparse
import json

from django.contrib import messages
from django.template.loader import render_to_string
from django.template import RequestContext
from django.core.urlresolvers import reverse, resolve
from django.db.models import get_model
from django.http import HttpResponseRedirect, Http404, HttpResponse
from django.views.generic import FormView, View
from django.utils.translation import ugettext_lazy as _
from django.core.exceptions import ObjectDoesNotExist

from extra_views import ModelFormSetView
from oscar.core import ajax
from oscar.apps.basket.signals import basket_addition, voucher_addition
from oscar.core.loading import get_class, get_classes
Applicator = get_class('offer.utils', 'Applicator')
(BasketLineFormSet, BasketLineForm, AddToBasketForm, BasketVoucherForm,
 SavedLineFormSet, SavedLineForm, ProductSelectionForm) \
    = get_classes('basket.forms', ('BasketLineFormSet', 'BasketLineForm',
                                   'AddToBasketForm', 'BasketVoucherForm',
                                   'SavedLineFormSet', 'SavedLineForm',
                                   'ProductSelectionForm'))
Repository = get_class('shipping.repository', ('Repository'))
OrderTotalCalculator = get_class(
    'checkout.calculators', 'OrderTotalCalculator')


def get_messages(basket, offers_before, offers_after,
                 include_buttons=True):
    """
    Return the messages about offer changes
    """
    # Look for changes in offers
    offers_lost = set(offers_before.keys()).difference(
        set(offers_after.keys()))
    offers_gained = set(offers_after.keys()).difference(
        set(offers_before.keys()))

    # Build a list of (level, msg) tuples
    offer_messages = []
    for offer_id in offers_lost:
        offer = offers_before[offer_id]
        msg = render_to_string(
            'basket/messages/offer_lost.html',
            {'offer': offer})
        offer_messages.append((
            messages.WARNING, msg))
    for offer_id in offers_gained:
        offer = offers_after[offer_id]
        msg = render_to_string(
            'basket/messages/offer_gained.html',
            {'offer': offer})
        offer_messages.append((
            messages.SUCCESS, msg))

    # We use the 'include_buttons' parameter to determine whether to show the
    # 'Checkout now' buttons.  We don't want to show these on the basket page.
    msg = render_to_string(
        'basket/messages/new_total.html',
        {'basket': basket,
         'include_buttons': include_buttons})
    offer_messages.append((
        messages.INFO, msg))

    return offer_messages


def apply_messages(request, offers_before):
    """
    Set flash messages triggered by changes to the basket
    """
    # Re-apply offers to see if any new ones are now available
    request.basket.reset_offer_applications()
    Applicator().apply(request, request.basket)
    offers_after = request.basket.applied_offers()

    for level, msg in get_messages(
            request.basket, offers_before, offers_after):
        messages.add_message(
            request, level, msg, extra_tags='safe noicon')


class BasketView(ModelFormSetView):
    model = get_model('basket', 'Line')
    basket_model = get_model('basket', 'Basket')
    formset_class = BasketLineFormSet
    form_class = BasketLineForm
    extra = 0
    can_delete = True
    template_name = 'basket/basket.html'

    def get_formset_kwargs(self):
        kwargs = super(BasketView, self).get_formset_kwargs()
        kwargs['strategy'] = self.request.strategy
        return kwargs

    def get_queryset(self):
        return self.request.basket.all_lines()

    def get_shipping_methods(self, basket):
        return Repository().get_shipping_methods(
            user=self.request.user, basket=self.request.basket,
            request=self.request)

    def get_default_shipping_method(self, basket):
        return Repository().get_default_shipping_method(
            user=self.request.user, basket=self.request.basket,
            request=self.request)

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
        applied_offers = basket.offer_applications.offers.values()
        msgs = []
        for offer in offers:
            if offer.is_condition_partially_satisfied(basket) \
                    and offer not in applied_offers:
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

        context['order_total'] = OrderTotalCalculator().calculate(
            self.request.basket, method)
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
                saved_basket.strategy = self.request.basket.strategy
                if not saved_basket.is_empty:
                    saved_queryset = saved_basket.all_lines().select_related(
                        'product', 'product__stockrecord')
                    formset = SavedLineFormSet(strategy=self.request.strategy,
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
        offers_before = self.request.basket.applied_offers()
        save_for_later = False

        # Keep a list of messages - we don't immediately call
        # django.contrib.messages as we may be returning an AJAX response in
        # which case we pass the messages back in a JSON payload.
        flash_messages = ajax.FlashMessages()

        for form in formset:
            if (hasattr(form, 'cleaned_data') and
                    form.cleaned_data['save_for_later']):
                line = form.instance
                if self.request.user.is_authenticated():
                    self.move_line_to_saved_basket(line)

                    msg = render_to_string(
                        'basket/messages/line_saved.html',
                        {'line': line})
                    flash_messages.info(msg)

                    save_for_later = True
                else:
                    msg = _("You can't save an item for later if you're "
                            "not logged in!")
                    messages.error(self.request, msg)
                    return HttpResponseRedirect(self.get_success_url())

        if save_for_later:
            # No need to call super if we're moving lines to the saved basket
            response = HttpResponseRedirect(self.get_success_url())
        else:
            # Save changes to basket as per normal
            response = super(BasketView, self).formset_valid(formset)

        # If AJAX submission, don't redirect but reload the basket content HTML
        if self.request.is_ajax():
            # Reload basket and apply offers again
            self.request.basket = get_model('basket', 'Basket').objects.get(
                id=self.request.basket.id)
            self.request.basket.strategy = self.request.strategy
            Applicator().apply(self.request, self.request.basket)
            offers_after = self.request.basket.applied_offers()

            for level, msg in get_messages(
                    self.request.basket, offers_before,
                    offers_after, include_buttons=False):
                flash_messages.add_message(level, msg)

            # Reload formset - we have to remove the POST fields from the
            # kwargs as, if they are left in, the formset won't construct
            # correctly as there will be a state mismatch between the
            # management form and the database.
            kwargs = self.get_formset_kwargs()
            del kwargs['data']
            del kwargs['files']
            if 'queryset' in kwargs:
                del kwargs['queryset']
            formset = self.get_formset()(queryset=self.get_queryset(),
                                         **kwargs)
            ctx = self.get_context_data(formset=formset,
                                        basket=self.request.basket)
            return self.json_response(ctx, flash_messages)

        apply_messages(self.request, offers_before)

        return response

    def json_response(self, ctx, flash_messages):
        basket_html = render_to_string(
            'basket/partials/basket_content.html',
            RequestContext(self.request, ctx))
        payload = {
            'content_html': basket_html,
            'messages': flash_messages.to_json()}
        return HttpResponse(json.dumps(payload),
                            content_type="application/json")

    def move_line_to_saved_basket(self, line):
        saved_basket, _ = get_model('basket', 'basket').saved.get_or_create(
            owner=self.request.user)
        saved_basket.merge_line(line)

    def formset_invalid(self, formset):
        flash_messages = ajax.FlashMessages()
        flash_messages.warning(_("Your basket couldn't be updated"))

        if self.request.is_ajax():
            ctx = self.get_context_data(formset=formset,
                                        basket=self.request.basket)
            return self.json_response(ctx, flash_messages)

        flash_messages.apply_to_request(self.request)
        return super(BasketView, self).formset_invalid(formset)


class BasketAddView(FormView):
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
        kwargs['request'] = self.request
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
        offers_before = self.request.basket.applied_offers()

        self.request.basket.add_product(
            form.instance, form.cleaned_data['quantity'],
            form.cleaned_options())

        messages.success(self.request, self.get_success_message(form),
                         extra_tags='safe noicon')

        # Check for additional offer messages
        apply_messages(self.request, offers_before)

        # Send signal for basket addition
        self.add_signal.send(
            sender=self, product=form.instance, user=self.request.user)

        return super(BasketAddView, self).form_valid(form)

    def get_success_message(self, form):
        return render_to_string(
            'basket/messages/addition.html',
            {'product': form.instance,
             'quantity': form.cleaned_data['quantity']})

    def form_invalid(self, form):
        msgs = []
        for error in form.errors.values():
            msgs.append(error.as_text())
        messages.error(self.request, ",".join(msgs))
        return HttpResponseRedirect(
            self.request.META.get('HTTP_REFERER', reverse('basket:summary')))


class VoucherAddView(FormView):
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
        discounts_after = self.request.basket.offer_applications

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


class VoucherRemoveView(View):
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


class SavedView(ModelFormSetView):
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
            saved_basket.strategy = self.request.strategy
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
        kwargs['strategy'] = self.request.strategy
        return kwargs

    def formset_valid(self, formset):
        offers_before = self.request.basket.applied_offers()

        is_move = False
        for form in formset:
            if form.cleaned_data.get('move_to_basket', False):
                is_move = True
                msg = render_to_string(
                    'basket/messages/line_restored.html',
                    {'line': form.instance})
                messages.info(self.request, msg, extra_tags='safe noicon')
                real_basket = self.request.basket
                real_basket.merge_line(form.instance)

        if is_move:
            # As we're changing the basket, we need to check if it qualifies
            # for any new offers.
            apply_messages(self.request, offers_before)
            response = HttpResponseRedirect(self.get_success_url())
        else:
            response = super(SavedView, self).formset_valid(formset)
        return response

    def formset_invalid(self, formset):
        messages.error(
            self.request,
            '\n'.join(
                error for ed in formset.errors for el
                in ed.values() for error in el))
        return HttpResponseRedirect(
            self.request.META.get('HTTP_REFERER', reverse('basket:summary')))
