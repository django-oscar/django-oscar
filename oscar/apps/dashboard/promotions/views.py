import itertools

from django.views import generic
from django.contrib.contenttypes.models import ContentType
from django.core.urlresolvers import reverse
from django.contrib import messages
from django.http import HttpResponseRedirect
from django.db.models import Count

from oscar.core.loading import get_classes, get_class
from oscar.apps.promotions.layout import split_by_position
from oscar.apps.promotions.conf import PROMOTION_CLASSES, PROMOTION_POSITIONS

SingleProduct, RawHTML, Image, MultiImage, \
    AutomaticProductList, PagePromotion, HandPickedProductList = get_classes('promotions.models',
    ['SingleProduct', 'RawHTML', 'Image', 'MultiImage', 'AutomaticProductList',
     'PagePromotion', 'HandPickedProductList'])
SelectForm, RawHTMLForm, PagePromotionForm = get_classes('dashboard.promotions.forms', 
    ['PromotionTypeSelectForm', 'RawHTMLForm', 'PagePromotionForm'])


class ListView(generic.TemplateView):
    template_name = 'dashboard/promotions/promotion_list.html'

    def get_context_data(self):
        # Need to load all promotions of all types and chain them together
        # no pagination required for now.
        data = []
        for klass in PROMOTION_CLASSES:
            data.append(klass.objects.all())
        promotions = itertools.chain(*data)                                    
        ctx = {
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
        pages = PagePromotion.objects.all().values('page_url').distinct().annotate(freq=Count('id'))
        return {'pages': pages}


class PageDetailView(generic.TemplateView):
    template_name = 'dashboard/promotions/page_detail.html'

    def get_context_data(self, *args, **kwargs):
        path = self.kwargs['path']
        ctx = {'page_url': path,
               'positions': self.get_positions_context_data(path),
              }
        return ctx

    def get_positions_context_data(self, path):
        ctx = []
        for code, name in PROMOTION_POSITIONS:
            promotions = PagePromotion._default_manager.select_related() \
                                                       .filter(page_url=path,
                                                               position=code) \
                                                       .order_by('display_order')
            ctx.append({
                'code': code,
                'name': name,
                'promotions': promotions,
            })
        return ctx


class PromotionMixin(object):

    def get_template_names(self):
        return ['dashboard/promotions/%s_form.html' % self.model.classname(),
                'dashboard/promotions/form.html']


class DeletePagePromotionView(generic.DeleteView):
    template_name = 'dashboard/promotions/delete-pagepromotion.html'
    model = PagePromotion

    def get_success_url(self):
        messages.info(self.request, "Promotion removed successfully")
        return reverse('dashboard:promotion-list-by-url', 
                       kwargs={'path': self.object.page_url})


# ============
# CREATE VIEWS
# ============


class CreateView(PromotionMixin, generic.CreateView):

    def get_success_url(self):
        messages.info(self.request, "Promotion created successfully")
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
        return 'Create a new %s content block' % self.model._type


class CreateRawHTMLView(CreateView):
    model = RawHTML
    form_class = RawHTMLForm


class CreateSingleProductView(CreateView):
    model = SingleProduct


class CreateImageView(CreateView):
    model = Image


class CreateAutomaticProductListView(CreateView):
    model = AutomaticProductList


class CreateHandPickedProductListView(CreateView):
    model = HandPickedProductList


# ============
# UPDATE VIEWS
# ============
        

class UpdateView(PromotionMixin, generic.UpdateView):
    actions = ('add_to_page', 'remove_from_page')
    link_form_class = PagePromotionForm

    def get_context_data(self, *args, **kwargs):
        ctx = super(UpdateView, self).get_context_data(*args, **kwargs)
        ctx['heading'] = "Update raw HTML block"
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
        messages.info(self.request, "Promotion updated successfully")
        return reverse('dashboard:promotion-list')

    def add_to_page(self, promotion, request, *args, **kwargs):
        instance = PagePromotion(content_object=self.get_object())
        form = self.link_form_class(request.POST, instance=instance)
        if form.is_valid():
            form.save()
            page_url = form.cleaned_data['page_url']
            messages.success(request, "Content block '%s' added to page '%s'" % (
                promotion.name, page_url))
            return HttpResponseRedirect(reverse('dashboard:promotion-update', kwargs=kwargs))

        main_form = self.get_form_class()(instance=self.object)
        ctx = self.get_context_data(form=main_form)
        ctx['link_form'] = form
        return self.render_to_response(ctx)

    def remove_from_page(self, promotion, request, *args, **kwargs):
        link_id = request.POST['pagepromotion_id']
        try:
            link = PagePromotion.objects.get(id=link_id)
        except PagePromotion.DoesNotExist:
            messages.error(request, "No link found to delete")
        else:
            page_url = link.page_url
            link.delete()
            messages.success(request, "Promotion removed from page '%s'" % page_url)
        return HttpResponseRedirect(reverse('dashboard:promotion-update', kwargs=kwargs))


class UpdateRawHTMLView(UpdateView):
    model = RawHTML
    form_class = RawHTMLForm


class UpdateSingleProductView(UpdateView):
    model = SingleProduct


class UpdateImageView(UpdateView):
    model = Image


class UpdateAutomaticProductListView(UpdateView):
    model = AutomaticProductList


class UpdateHandPickedProductListView(UpdateView):
    model = HandPickedProductList


# ============
# DELETE VIEWS
# ============
        

class DeleteView(generic.DeleteView):
    template_name = 'dashboard/promotions/delete.html'

    def get_success_url(self):
        messages.info(self.request, "Promotion deleted successfully")
        return reverse('dashboard:promotion-list')


class DeleteRawHTMLView(DeleteView):
    model = RawHTML


class DeleteSingleProductView(DeleteView):
    model = SingleProduct


class DeleteImageView(DeleteView):
    model = Image


class DeleteAutomaticProductListView(DeleteView):
    model = AutomaticProductList


class DeleteHandPickedProductListView(DeleteView):
    model = HandPickedProductList
