from django.contrib import messages
from django.core.urlresolvers import reverse
from django.db.models import get_model
from django.http import HttpResponseRedirect, Http404
from django.views.generic import ListView, FormView
from extra_views import ModelFormsetView
from oscar.apps.basket.forms import BasketLineForm, AddToBasketForm, \
    BasketVoucherForm


class BasketView(ModelFormsetView):
    model = get_model('basket', 'line')
    form_class = BasketLineForm
    extra = 0
    can_delete = True
    template_name='basket/basket.html'
    
    def get_context_data(self, **kwargs):
        context = super(BasketView, self).get_context_data(**kwargs)
        context['voucher_form'] = BasketVoucherForm()
        return context

    def formset_valid(self, formset):
        messages.info(self.request, "Basket Updated.")
        needs_auth = False
        for form in formset:
            if form.cleaned_data['save_for_later']:
                instance = form.instance
                if self.request.user.is_authenticated():
                    saved_basket, _ = get_model('basket','basket').saved.get_or_create(owner=self.request.user)
                    saved_basket.merge_line(instance)
                    messages.info(self.request, "'%s' has been saved for later" % instance.product)   
                else:
                    needs_auth = True
        if needs_auth:
            messages.error(self.request, "You can't save an item for later if you're not logged in!")     
        
        return HttpResponseRedirect(self.request.META.get('HTTP_REFERER',reverse('basket')))
    
    def formset_invalid(self, formset):
        messages.info(self.request, "There was a problem updating your basket, please check that all quantities are numbers")


class BasketAddView(FormView):
    u"""
    Handles the add-to-basket operation, shouldn't be accessed via GET because there's nothing sensible to render.
    """
    form_class = AddToBasketForm
    product_model = get_model('product', 'item')
    
    def get(self, request, *args, **kwargs):
        return HttpResponseRedirect(reverse('basket'))
    
    def get_form_kwargs(self): 
        kwargs = super(BasketAddView, self).get_form_kwargs()
        
        try:
            product = self.product_model.objects.get(pk=self.request.POST['product_id'])
        except self.product_model.DoesNotExist:
            raise Http404()
        kwargs['instance'] = product
        return kwargs

    def form_valid(self, form):
        options = []
        for option in form.instance.options:
            if option.code in form.cleaned_data:
                options.append({'option': option, 'value': form.cleaned_data[option.code]})
        self.request.basket.add_product(form.instance, form.cleaned_data['quantity'], options)
        messages.info(self.request, "'%s' (quantity %d) has been added to your basket" %
                      (form.instance.get_title(), form.cleaned_data['quantity']))
        return HttpResponseRedirect(self.request.META.get('HTTP_REFERER',reverse('basket')))
    
    def form_invalid(self, form):
        return HttpResponseRedirect(self.request.META.get('HTTP_REFERER',reverse('basket')))


class VoucherView(ListView):
    model = get_model('offer', 'voucher')
    can_delete = True
    extra = 0
    
    def get_queryset(self):
        self.request.basket.vouchers.all()


class VoucherAddView(FormView):
    form_class = BasketVoucherForm
    voucher_model = get_model('offer', 'voucher')
    
    def get(self, request, *args, **kwargs):
        return HttpResponseRedirect(reverse('basket'))
    
    def _check_voucher(self, code):
        try:
            voucher = self.request.basket.vouchers.get(code=code)
            messages.error(self.request, "You have already added the '%s' voucher to your basket" % voucher.code)
            return
        except self.voucher_model.DoesNotExist:    
            pass
        try:
            voucher = self.voucher_model._default_manager.get(code=code)
            if not voucher.is_active():
                messages.error(self.request, "The '%s' voucher has expired" % voucher.code)
                return
            is_available, message = voucher.is_available_to_user(self.request.user)
            if not is_available:
                messages.error(self.request, message)
                return
            self.request.basket.vouchers.add(voucher)
            self.request.basket.save()
            messages.info(self.request, "Voucher '%s' added to basket" % voucher.code)
        except self.voucher_model.DoesNotExist:
            messages.error(self.request, "No voucher found with code '%s'" % code)
    
    def form_valid(self, form):
        code = form.cleaned_data['code']
        self._check_voucher(code)
        return HttpResponseRedirect(self.request.META.get('HTTP_REFERER', reverse('basket')))
    
    def form_invalid(self, form):
        return HttpResponseRedirect(reverse('basket'))


class SavedView(ListView):
    template_name = 'basket/saved_list.html'
    context_object_name = "saved_items" 
    basket_model = get_model('basket', 'basket')
    allow_empty = True
    paginate_by = 20
     
    def get_queryset(self):
        try:
            saved_basket = self.basket_model.saved.get(owner=self.request.user)
            return saved_basket.lines.all().select_related('product', 'product__stockrecord')
        except self.basket_model.DoesNotExist:
            return []


#    def do_remove_voucher(self, basket):
#        code = self.request.POST['voucher_code']
#        try:
#            voucher = basket.vouchers.get(code=code)
#            basket.vouchers.remove(voucher)
#            basket.save()
#            messages.info(self.request, "Voucher '%s' removed from basket" % voucher.code)
#        except ObjectDoesNotExist:
#            messages.error(self.request, "No voucher found with code '%s'" % code)
#            
#    def do_bulk_load(self, basket):
#        num_additions = 0
#        num_not_found = 0
#        for sku in re.findall(r"[\d -]{5,}", self.request.POST['source_text']):
#            try:
#                item = Item.objects.get(upc=sku)
#                basket.add_product(item)
#                num_additions += 1
#            except Item.DoesNotExist:
#                num_not_found += 1
#        messages.info(self.request, "Added %d items to your basket (%d missing)" % (num_additions, num_not_found))
#