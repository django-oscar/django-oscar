# -*- coding: utf-8 -*-
from django.contrib import messages
from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned
from django.core.urlresolvers import reverse
from django.db.models import get_model
from django.http import Http404, HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, View, FormView
from django.utils.translation import ugettext_lazy as _
from oscar.apps.customer.mixins import PageTitleMixin
from .forms import WishListForm, LineFormset

WishList = get_model('wishlists', 'WishList')
Line = get_model('wishlists', 'Line')
Product = get_model('catalogue', 'Product')


class WishListListView(PageTitleMixin, ListView):
    context_object_name = active_tab = "wishlists"
    template_name = 'customer/wishlists/wishlists_list.html'
    page_title = _('Wish Lists')

    def get_queryset(self):
        return WishList._default_manager.filter(owner=self.request.user)


class WishListDetailView(PageTitleMixin, FormView):
    """
    This view acts as a DetailView for a wish list and allows updating the
    quantities of products.
    It is implemented as FormView because it's easier to adapt a FormView to
    display a product then adapt a DetailView to handle form validation.
    """
    template_name = 'customer/wishlists/wishlists_detail.html'
    active_tab = "wishlists"
    form_class = LineFormset

    def dispatch(self, request, *args, **kwargs):
        self.object = self.get_wishlist_or_404(kwargs['key'], request.user)
        return super(WishListDetailView, self).dispatch(request, *args, **kwargs)

    def get_wishlist_or_404(self, key, user):
        wishlist = get_object_or_404(WishList, key=key)
        if wishlist.is_allowed_to_see(user):
            return wishlist
        else:
            raise Http404

    def get_page_title(self):
        return self.object.name

    def get_form_kwargs(self):
        kwargs = super(WishListDetailView, self).get_form_kwargs()
        kwargs['instance'] = self.object
        return kwargs

    def get_context_data(self, **kwargs):
        ctx = super(WishListDetailView, self).get_context_data(**kwargs)
        ctx['wishlist'] = self.object
        other_wishlists = self.request.user.wishlists.exclude(
            pk=self.object.pk)
        ctx['other_wishlists'] = other_wishlists
        return ctx

    def form_valid(self, form):
        for subform in form:
            if subform.cleaned_data['quantity'] <= 0:
                subform.instance.delete()
            else:
                subform.save()
        messages.success(self.request, _('Quantities updated.'))
        return HttpResponseRedirect(reverse('customer:wishlists-detail',
                                            kwargs= {'key': self.object.key}))


class WishListCreateView(PageTitleMixin, CreateView):
    model = WishList
    template_name = 'customer/wishlists/wishlists_form.html'
    active_tab = "wishlists"
    page_title = _('Create new Wish List')
    form_class = WishListForm

    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.owner = self.request.user
        self.object.save()
        if 'product_pk' in self.kwargs:
            try:
                product = Product.objects.get(pk=self.kwargs['product_pk'])
            except (ObjectDoesNotExist, MultipleObjectsReturned):
                pass
            else:
                title = product.get_title()
                line = Line.objects.create(product=product,
                                           wishlist=self.object,
                                           title=title)
                messages.success(self.request,
                                 _("'%s' was added to your wish list.") % title)
        return HttpResponseRedirect(self.get_success_url())

    def get_success_url(self):
        messages.success(self.request, _("Wish list '%s' created") %
                                       self.object.name)
        return reverse('customer:wishlists-list')


class WishListUpdateView(PageTitleMixin, UpdateView):
    model = WishList
    template_name = 'customer/wishlists/wishlists_form.html'
    active_tab = "wishlists"
    form_class = WishListForm

    def get_page_title(self):
        return u'Edit %s' % self.object.name

    def get_object(self, queryset=None):
        return get_object_or_404(WishList, owner=self.request.user,
                                 key=self.kwargs['key'])

    def get_success_url(self):
        messages.success(self.request, _("Changes saved"))
        return reverse('customer:wishlists-list')


class WishListDeleteView(PageTitleMixin, DeleteView):
    model = WishList
    template_name = 'customer/wishlists/wishlists_delete.html'
    active_tab = "wishlists"

    def get_page_title(self):
        return u'Delete %s' % self.object.name

    def get_object(self, queryset=None):
        return get_object_or_404(WishList, owner=self.request.user,
                                 key=self.kwargs['key'])

    def get_success_url(self):
        messages.success(self.request, _("Wish list deleted"))
        return reverse('customer:wishlists-list')


class WishListAddProduct(View):
    """
    Adds a product to a wish list. If no wish list is passed, it is created.
    If the product is already in the wish list, it's quantity is increased.
    """

    def get(self, request, *args, **kwargs):
        product = get_object_or_404(Product, pk=kwargs['product_pk'])
        wishlist = get_object_or_404(WishList, owner=request.user,
                                     key=kwargs['key'])
        if not wishlist.is_allowed_to_edit(self.request.user):
            raise Http404
        try:
            line = wishlist.lines.get(product=product)
        except ObjectDoesNotExist:
            line = Line.objects.create(product=product, wishlist=wishlist,
                                       title=product.get_title())
            msg = _("'%s' was added to your wish list.")
        else:
            line.quantity += 1
            line.save()
            msg = _("The quantity of '%s' in your wish list was increased.")

        messages.success(self.request, msg % product)
        return HttpResponseRedirect(product.get_absolute_url())


class LineMixin(object):
    """
    Handles fetching both a wish list and a product
    Views using this mixin must be passed two keyword arguments:
    * key: The key of a wish list

    * line_pk: The primary key of the wish list line
    or
    * product_pk: The primary key of the product
    """

    def dispatch(self, request, *args, **kwargs):
        self.wishlist = get_object_or_404(WishList, owner=request.user,
                                          key=kwargs['key'])
        try:
            if 'line_pk' in kwargs:
                self.line = self.wishlist.lines.get(pk=kwargs['line_pk'])
            elif 'product_pk' in kwargs:
                self.line = self.wishlist.lines.get(product_id=kwargs['product_pk'])
        except (ObjectDoesNotExist, MultipleObjectsReturned):
            raise Http404

        self.product = self.line.product
        return super(LineMixin, self).dispatch(request, *args, **kwargs)


class WishListRemoveProduct(LineMixin, View):

    def get(self, request, *args, **kwargs):
        self.line.delete()
        messages.success(self.request, _('Product removed from wish list %s') %
                         self.wishlist.name)
        default_url = reverse('customer:wishlists-detail',
                              kwargs= {'key': self.wishlist.key})
        return HttpResponseRedirect(self.request.META.get('HTTP_REFERER',
                                                          default_url))


class WishListMoveProductToAnotherWishList(LineMixin, View):

    def get(self, request, *args, **kwargs):
        #from_wishlist = self.wishlist
        to_wishlist = get_object_or_404(WishList, owner=request.user,
                                        key=kwargs['to_key'])
        self.line.wishlist = to_wishlist
        self.line.save()
        messages.success(self.request,
                         _('Product moved to wish list %s') % to_wishlist.name)
        default_url = reverse('customer:wishlists-detail',
                              kwargs= {'key': self.wishlist.key})
        return HttpResponseRedirect(self.request.META.get('HTTP_REFERER',
                                                          default_url))



