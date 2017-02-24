import itertools

from django.conf import settings
from django.contrib import messages
from django.contrib.contenttypes.models import ContentType
from django.core.urlresolvers import reverse
from django.db.models import Count
from django.http import HttpResponseRedirect
from django.shortcuts import HttpResponse
from django.utils.translation import ugettext_lazy as _
from django.views import generic

from oscar.apps.promotions.conf import PROMOTION_CLASSES
from oscar.core.loading import get_classes

SingleProduct, RawHTML, Image, MultiImage, AutomaticProductList, \
    PagePromotion, HandPickedProductList \
    = get_classes('promotions.models',
                  ['SingleProduct', 'RawHTML', 'Image', 'MultiImage',
                   'AutomaticProductList', 'PagePromotion',
                   'HandPickedProductList'])
SelectForm, RawHTMLForm, PagePromotionForm, HandPickedProductListForm, \
    SingleProductForm, OrderedProductFormSet \
    = get_classes('dashboard.promotions.forms',
                  ['PromotionTypeSelectForm', 'RawHTMLForm',
                   'PagePromotionForm', 'HandPickedProductListForm',
                   'SingleProductForm', 'OrderedProductFormSet'])


class ListView(generic.TemplateView):
    template_name = 'dashboard/promotions/promotion_list.html'

    def get_context_data(self):
        # Need to load all promotions of all types and chain them together
        # no pagination required for now.
        data = []
        num_promotions = 0
        for klass in PROMOTION_CLASSES:
            objects = klass.objects.all()
            num_promotions += objects.count()
            data.append(objects)
        promotions = itertools.chain(*data)
        ctx = {
            'num_promotions': num_promotions,
            'promotions': promotions,
            'select_form': SelectForm(),
        }
        return ctx


class CreateRedirectView(generic.RedirectView):
    permanent = True

    def get_redirect_url(self, **kwargs):
        code = self.request.GET.get('promotion_type', None)
        urls = {}
        for klass in PROMOTION_CLASSES:
            urls[klass.classname()] = reverse('dashboard:promotion-create-%s' %
                                              klass.classname())
        return urls.get(code, None)


class PageListView(generic.TemplateView):
    template_name = 'dashboard/promotions/pagepromotion_list.html'

    def get_context_data(self, *args, **kwargs):
        pages = PagePromotion.objects.all().values(
            'page_url').distinct().annotate(freq=Count('id'))
        return {'pages': pages}


class PageDetailView(generic.TemplateView):
    template_name = 'dashboard/promotions/page_detail.html'

    def get_context_data(self, *args, **kwargs):
        path = self.kwargs['path']
        return {'page_url': path,
                'positions': self.get_positions_context_data(path), }

    def get_positions_context_data(self, path):
        ctx = []
        for code, name in settings.OSCAR_PROMOTION_POSITIONS:
            promotions = PagePromotion._default_manager.select_related() \
                                                       .filter(page_url=path,
                                                               position=code)
            ctx.append({
                'code': code,
                'name': name,
                'promotions': promotions.order_by('display_order'),
            })
        return ctx

    def post(self, request, **kwargs):
        """
        When called with a post request, try and get 'promo' from
        the post data and use it to reorder the page content blocks.
        """
        data = dict(request.POST).get('promo')
        self._save_page_order(data)
        return HttpResponse(status=200)

    def _save_page_order(self, data):
        """
        Save the order of the pages. This gets used when an ajax request
        posts backa new order for promotions within page regions.
        """
        for index, item in enumerate(data):
            page = PagePromotion.objects.get(pk=item)
            if page.display_order != index:
                page.display_order = index
                page.save()


class PromotionMixin(object):

    def get_template_names(self):
        return ['dashboard/promotions/%s_form.html' % self.model.classname(),
                'dashboard/promotions/form.html']


class DeletePagePromotionView(generic.DeleteView):
    template_name = 'dashboard/promotions/delete_pagepromotion.html'
    model = PagePromotion

    def get_success_url(self):
        messages.info(self.request, _("Content block removed successfully"))
        return reverse('dashboard:promotion-list-by-url',
                       kwargs={'path': self.object.page_url})


# ============
# CREATE VIEWS
# ============


class CreateView(PromotionMixin, generic.CreateView):

    def get_success_url(self):
        messages.success(self.request, _("Content block created successfully"))
        return reverse('dashboard:promotion-update',
                       kwargs={'ptype': self.model.classname(),
                               'pk': self.object.id})

    def get_context_data(self, *args, **kwargs):
        ctx = super(CreateView, self).get_context_data(*args, **kwargs)
        ctx['heading'] = self.get_heading()
        return ctx

    def get_heading(self):
        if hasattr(self, 'heading'):
            return getattr(self, 'heading')
        return _('Create a new %s content block') % self.model._type


class CreateRawHTMLView(CreateView):
    model = RawHTML
    form_class = RawHTMLForm


class CreateSingleProductView(CreateView):
    model = SingleProduct
    form_class = SingleProductForm


class CreateImageView(CreateView):
    model = Image
    fields = ['name', 'link_url', 'image']


class CreateMultiImageView(CreateView):
    model = MultiImage
    fields = ['name']


class CreateAutomaticProductListView(CreateView):
    model = AutomaticProductList
    fields = ['name', 'description', 'link_url', 'link_text', 'method',
              'num_products']


class CreateHandPickedProductListView(CreateView):
    model = HandPickedProductList
    form_class = HandPickedProductListForm

    def get_context_data(self, **kwargs):
        ctx = super(CreateHandPickedProductListView,
                    self).get_context_data(**kwargs)
        if 'product_formset' not in kwargs:
            ctx['product_formset'] \
                = OrderedProductFormSet(instance=self.object)
        return ctx

    def form_valid(self, form):
        promotion = form.save(commit=False)
        product_formset = OrderedProductFormSet(self.request.POST,
                                                instance=promotion)
        if product_formset.is_valid():
            promotion.save()
            product_formset.save()
            self.object = promotion
            messages.success(self.request,
                             _('Product list content block created'))
            return HttpResponseRedirect(self.get_success_url())

        ctx = self.get_context_data(product_formset=product_formset)
        return self.render_to_response(ctx)


# ============
# UPDATE VIEWS
# ============


class UpdateView(PromotionMixin, generic.UpdateView):
    actions = ('add_to_page', 'remove_from_page')
    link_form_class = PagePromotionForm

    def get_context_data(self, *args, **kwargs):
        ctx = super(UpdateView, self).get_context_data(*args, **kwargs)
        ctx['heading'] = _("Update content block")
        ctx['promotion'] = self.get_object()
        ctx['link_form'] = self.link_form_class()
        content_type = ContentType.objects.get_for_model(self.model)
        ctx['links'] = PagePromotion.objects.filter(content_type=content_type,
                                                    object_id=self.object.id)
        return ctx

    def post(self, request, *args, **kwargs):
        action = request.POST.get('action', None)
        if action in self.actions:
            self.object = self.get_object()
            return getattr(self, action)(self.object, request, *args, **kwargs)
        return super(UpdateView, self).post(request, *args, **kwargs)

    def get_success_url(self):
        messages.info(self.request, _("Content block updated successfully"))
        return reverse('dashboard:promotion-list')

    def add_to_page(self, promotion, request, *args, **kwargs):
        instance = PagePromotion(content_object=self.get_object())
        form = self.link_form_class(request.POST, instance=instance)
        if form.is_valid():
            form.save()
            page_url = form.cleaned_data['page_url']
            messages.success(request, _("Content block '%(block)s' added to"
                                        " page '%(page)s'")
                             % {'block': promotion.name,
                                'page': page_url})
            return HttpResponseRedirect(reverse('dashboard:promotion-update',
                                                kwargs=kwargs))

        main_form = self.get_form_class()(instance=self.object)
        ctx = self.get_context_data(form=main_form)
        ctx['link_form'] = form
        return self.render_to_response(ctx)

    def remove_from_page(self, promotion, request, *args, **kwargs):
        link_id = request.POST['pagepromotion_id']
        try:
            link = PagePromotion.objects.get(id=link_id)
        except PagePromotion.DoesNotExist:
            messages.error(request, _("No link found to delete"))
        else:
            page_url = link.page_url
            link.delete()
            messages.success(request, _("Content block removed from page '%s'")
                             % page_url)
        return HttpResponseRedirect(reverse('dashboard:promotion-update',
                                            kwargs=kwargs))


class UpdateRawHTMLView(UpdateView):
    model = RawHTML
    form_class = RawHTMLForm


class UpdateSingleProductView(UpdateView):
    model = SingleProduct
    form_class = SingleProductForm


class UpdateImageView(UpdateView):
    model = Image
    fields = ['name', 'link_url', 'image']


class UpdateMultiImageView(UpdateView):
    model = MultiImage
    fields = ['name', 'images']


class UpdateAutomaticProductListView(UpdateView):
    model = AutomaticProductList
    fields = ['name', 'description', 'link_url', 'link_text', 'method',
              'num_products']


class UpdateHandPickedProductListView(UpdateView):
    model = HandPickedProductList
    form_class = HandPickedProductListForm

    def get_context_data(self, **kwargs):
        ctx = super(UpdateHandPickedProductListView,
                    self).get_context_data(**kwargs)
        if 'product_formset' not in kwargs:
            ctx['product_formset'] \
                = OrderedProductFormSet(instance=self.object)
        return ctx

    def form_valid(self, form):
        promotion = form.save(commit=False)
        product_formset = OrderedProductFormSet(self.request.POST,
                                                instance=promotion)
        if product_formset.is_valid():
            promotion.save()
            product_formset.save()
            self.object = promotion
            messages.success(self.request, _('Product list promotion updated'))
            return HttpResponseRedirect(self.get_success_url())

        ctx = self.get_context_data(product_formset=product_formset)
        return self.render_to_response(ctx)

# ============
# DELETE VIEWS
# ============


class DeleteView(generic.DeleteView):
    template_name = 'dashboard/promotions/delete.html'

    def get_success_url(self):
        messages.info(self.request, _("Content block deleted successfully"))
        return reverse('dashboard:promotion-list')


class DeleteRawHTMLView(DeleteView):
    model = RawHTML


class DeleteSingleProductView(DeleteView):
    model = SingleProduct


class DeleteImageView(DeleteView):
    model = Image


class DeleteMultiImageView(DeleteView):
    model = MultiImage


class DeleteAutomaticProductListView(DeleteView):
    model = AutomaticProductList


class DeleteHandPickedProductListView(DeleteView):
    model = HandPickedProductList
