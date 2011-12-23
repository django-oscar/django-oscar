from django.contrib import messages
from django.core.urlresolvers import reverse
from django.db.models import get_model
from django.http import HttpResponseRedirect, Http404
from django.views.generic import ListView, FormView, View
from django.forms.models import modelformset_factory
from django.utils.translation import ugettext_lazy as _
from django.core.exceptions import ObjectDoesNotExist

from extra_views import ModelFormSetView
from oscar.apps.basket.forms import BasketLineForm, AddToBasketForm, \
    BasketVoucherForm, SavedLineForm, ProductSelectionForm
from oscar.apps.basket.signals import basket_addition
from oscar.core.loading import import_module
import_module('offer.utils', ['Applicator'], locals())


class BasketView(ModelFormSetView):
    model = get_model('basket', 'Line')
    basket_model = get_model('basket', 'Basket')
    form_class = BasketLineForm
    extra = 0
    can_delete = True
    template_name='basket/basket.html'

    def get_queryset(self):
        return self.request.basket.lines.all()

    def get_context_data(self, **kwargs):
        context = super(BasketView, self).get_context_data(**kwargs)
        context['voucher_form'] = BasketVoucherForm()

        if self.request.user.is_authenticated():
            try:
                saved_basket = self.basket_model.saved.get(owner=self.request.user)
                saved_queryset = saved_basket.lines.all().select_related('product', 'product__stockrecord')
                SavedFormset = modelformset_factory(self.model, form=SavedLineForm, extra=0, can_delete=True)
                formset = SavedFormset(queryset=saved_queryset)
                context['saved_formset'] = formset
            except self.basket_model.DoesNotExist:
                pass
        return context

    def get_success_url(self):
        return self.request.META.get('HTTP_REFERER', reverse('basket:summary'))

    def formset_valid(self, formset):
        needs_auth = False
        for form in formset:
            if form.cleaned_data['save_for_later']:
                line = form.instance
                if self.request.user.is_authenticated():
                    self.move_line_to_saved_basket(line)
                    messages.info(self.request, _(u"'%(title)s' has been saved for later" % {'title': line.product}))
                else:
                    needs_auth = True
        if needs_auth:
            messages.error(self.request, "You can't save an item for later if you're not logged in!")
        return super(BasketView, self).formset_valid(formset)

    def move_line_to_saved_basket(self, line):
        saved_basket, _ = get_model('basket', 'basket').saved.get_or_create(owner=self.request.user)
        saved_basket.merge_line(line)

    def formset_invalid(self, formset):
        messages.info(self.request, _("There was a problem updating your basket, please check that all quantities are numbers"))
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
            raise Http404()
        kwargs['basket'] = self.request.basket
        return kwargs

    def get_success_url(self):
        return self.request.META.get('HTTP_REFERER', reverse('basket:summary'))

    def form_valid(self, form):
        options = []
        for option in form.instance.options:
            if option.code in form.cleaned_data:
                options.append({'option': option, 'value': form.cleaned_data[option.code]})
        self.request.basket.add_product(form.instance, form.cleaned_data['quantity'], options)
        messages.info(self.request, _(u"'%(title)s' (quantity %(quantity)d) has been added to your basket" %
                {'title': form.instance.get_title(),
                 'quantity': form.cleaned_data['quantity']}))

        # Send signal for basket addition
        self.add_signal.send(sender=self, product=form.instance, user=self.request.user)

        return super(BasketAddView, self).form_valid(form)

    def form_invalid(self, form):
        msgs = []
        for error in form.errors.values():
            msgs.append(error.as_text())
        messages.error(self.request, ",".join(msgs))
        return HttpResponseRedirect(self.request.META.get('HTTP_REFERER',reverse('basket:summary')))


class VoucherAddView(FormView):
    form_class = BasketVoucherForm
    voucher_model = get_model('voucher', 'voucher')

    def get(self, request, *args, **kwargs):
        return HttpResponseRedirect(reverse('basket:summary'))

    def apply_voucher_to_basket(self, voucher):
        if not voucher.is_active():
            messages.error(self.request, _("The '%(code)s' voucher has expired" % {'code': voucher.code}))
            return

        is_available, message = voucher.is_available_to_user(self.request.user)
        if not is_available:
            messages.error(self.request, message)
            return

        self.request.basket.vouchers.add(voucher)

        # Recalculate discounts to see if the voucher gives any
        discounts_before = self.request.basket.get_discounts()
        self.request.basket.remove_discounts()
        Applicator().apply(self.request, self.request.basket)
        discounts_after = self.request.basket.get_discounts()

        # Look for discounts from this new voucher
        found_discount = False
        for discount in discounts_after:
            if discount['voucher'] and discount['voucher'] == voucher:
                found_discount = True
                break
        if not found_discount:
            messages.warning(self.request, _("Your basket does not qualify for a voucher discount"))
            self.request.basket.vouchers.remove(voucher)
        else:
            messages.info(self.request, _("Voucher '%(code)s' added to basket" % {'code': voucher.code}))

    def form_valid(self, form):
        code = form.cleaned_data['code']
        if not self.request.basket.id:
            return HttpResponseRedirect(self.request.META.get('HTTP_REFERER', reverse('basket:summary')))
        if self.request.basket.contains_voucher(code):
            messages.error(self.request, _("You have already added the '%(code)s' voucher to your basket" % {'code': code}))
        else:
            try:
                voucher = self.voucher_model._default_manager.get(code=code)
            except self.voucher_model.DoesNotExist:
                messages.error(self.request, _("No voucher found with code '%(code)s'" % {'code': code}))
            else:
                self.apply_voucher_to_basket(voucher)
        return HttpResponseRedirect(self.request.META.get('HTTP_REFERER', reverse('basket:summary')))

    def form_invalid(self, form):
        return HttpResponseRedirect(reverse('basket:summary'))


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
            messages.error(request, "No voucher found with id '%d'" % voucher_id)
        else:
            request.basket.vouchers.remove(voucher)
            request.basket.save()
            messages.info(request, "Voucher '%s' removed from basket" % voucher.code)
        return HttpResponseRedirect(reverse('basket:summary'))


class SavedView(ModelFormSetView):
    model = get_model('basket', 'line')
    basket_model = get_model('basket', 'basket')
    form_class = SavedLineForm
    extra = 0
    can_delete = True

    def get(self, request, *args, **kwargs):
        return HttpResponseRedirect(reverse('basket:summary'))

    def get_queryset(self):
        try:
            saved_basket = self.basket_model.saved.get(owner=self.request.user)
            return saved_basket.lines.all().select_related('product', 'product__stockrecord')
        except self.basket_model.DoesNotExist:
            return []

    def get_success_url(self):
        return self.request.META.get('HTTP_REFERER', reverse('basket:summary'))

    def formset_valid(self, formset):
        for form in formset:
            if form.cleaned_data['move_to_basket']:
                msg = "'%s' has been moved back to your basket" % form.instance.product
                messages.info(self.request, msg)
                real_basket = self.request.basket
                real_basket.merge_line(form.instance)
        return super(SavedView, self).formset_valid(formset)

    def formset_invalid(self, formset):
        return HttpResponseRedirect(self.request.META.get('HTTP_REFERER', reverse('basket:summary')))



#    def do_bulk_load(self, basket):
#        num_additions = 0
#        num_not_found = 0
#        for sku in re.findall(r"[\d -]{5,}", self.request.POST['source_text']):
#            try:
#                item = Product.objects.get(upc=sku)
#                basket.add_product(item)
#                num_additions += 1
#            except Product.DoesNotExist:
#                num_not_found += 1
#        messages.info(self.request, "Added %d items to your basket (%d missing)" % (num_additions, num_not_found))
#