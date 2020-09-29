from django.contrib import messages
from django.core.exceptions import ObjectDoesNotExist
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.views.generic import FormView, View

from oscar.apps.voucher.signals import voucher_addition, voucher_removal
from oscar.core.loading import get_class, get_model
from oscar.core.utils import redirect_to_referrer

Applicator = get_class('offer.applicator', 'Applicator')
BasketVoucherForm = get_class('voucher.forms', 'BasketVoucherForm')


class VoucherAddView(FormView):
    form_class = BasketVoucherForm
    voucher_model = get_model('voucher', 'voucher')
    add_signal = voucher_addition

    def get(self, request, *args, **kwargs):
        return redirect('basket:summary')

    def apply_voucher_to_basket(self, voucher):
        if voucher.is_expired():
            messages.error(
                self.request,
                _("The '%(code)s' voucher has expired") % {
                    'code': voucher.code})
            return

        if not voucher.is_active():
            messages.error(
                self.request,
                _("The '%(code)s' voucher is not active") % {
                    'code': voucher.code})
            return

        is_available, message = voucher.is_available_to_user(self.request.user)
        if not is_available:
            messages.error(self.request, message)
            return

        self.request.basket.vouchers.add(voucher)

        # Raise signal
        self.add_signal.send(
            sender=self, basket=self.request.basket, voucher=voucher)

        # Recalculate discounts to see if the voucher gives any
        Applicator().apply(self.request.basket, self.request.user,
                           self.request)
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
            return redirect_to_referrer(self.request, 'basket:summary')
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
        return redirect_to_referrer(self.request, 'basket:summary')

    def form_invalid(self, form):
        messages.error(self.request, _("Please enter a voucher code"))
        return redirect(reverse('basket:summary') + '#voucher')


class VoucherRemoveView(View):
    voucher_model = get_model('voucher', 'voucher')
    remove_signal = voucher_removal
    http_method_names = ['post']

    def post(self, request, *args, **kwargs):
        response = redirect('basket:summary')

        voucher_id = kwargs['pk']
        if not request.basket.id:
            # Hacking attempt - the basket must be saved for it to have
            # a voucher in it.
            return response
        try:
            voucher = request.basket.vouchers.get(id=voucher_id)
        except ObjectDoesNotExist:
            messages.error(
                request, _("No voucher found with id '%s'") % voucher_id)
        else:
            request.basket.vouchers.remove(voucher)
            self.remove_signal.send(
                sender=self, basket=request.basket, voucher=voucher)
            messages.info(
                request, _("Voucher '%s' removed from basket") % voucher.code)

        return response
