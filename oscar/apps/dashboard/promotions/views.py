import itertools

from django.views import generic
from django.contrib.contenttypes.models import ContentType
from django.core.urlresolvers import reverse
from django.contrib import messages
from django.http import HttpResponseRedirect
from django.db.models import Count

from oscar.core.loading import get_classes, get_class

SingleProduct, RawHTML, Image, MultiImage, PagePromotion = get_classes('promotions.models',
    ['SingleProduct', 'RawHTML', 'Image', 'MultiImage', 'PagePromotion'])
SelectForm, RawHTMLForm, PagePromotionForm = get_classes('dashboard.promotions.forms', 
    ['PromotionTypeSelectForm', 'RawHTMLForm', 'PagePromotionForm'])


class PromotionListView(generic.TemplateView):
    template_name = 'dashboard/promotions/promotion_list.html'

    def get_context_data(self):
        # Need to load all promotions of all types and chain them together
        # no pagination required for now.
        promotions = itertools.chain(SingleProduct.objects.all(),
                                     RawHTML.objects.all(),
                                     Image.objects.all(),
                                     MultiImage.objects.all(),
                                    )
        ctx ={
            'promotions': promotions,
            'select_form': SelectForm(),
        }
        return ctx


class PromotionCreateRedirectView(generic.RedirectView):
    permanent = True

    def get_redirect_url(self, **kwargs):
        code = self.request.GET.get('promotion_type', None)
        urls = {
            'rawhtml': reverse('dashboard:promotion-create-rawhtml')
        }
        return urls.get(code, None)


class PromotionPageListView(generic.TemplateView):
    template_name = 'dashboard/promotions/pagepromotion_list.html'

    def get_context_data(self, *args, **kwargs):
        pages = PagePromotion.objects.all().values('page_url').distinct().annotate(freq=Count('id'))
        return {'pages': pages}




# ============
# CREATE VIEWS
# ============

class PromotionCreateView(generic.CreateView):

    def get_success_url(self):
        messages.info(self.request, "Promotion created successfully")
        return reverse('dashboard:promotion-list')


class PromotionCreateRawHTMLView(PromotionCreateView):
    template_name = 'dashboard/promotions/rawhtml_form.html'
    model = RawHTML
    form_class = RawHTMLForm

    def get_context_data(self, *args, **kwargs):
        ctx = super(PromotionCreateRawHTMLView, self).get_context_data(*args, **kwargs)
        ctx['heading'] = 'Create a new raw HTML block'
        return ctx


# ============
# UPDATE VIEWS
# ============
        

class PromotionUpdateView(generic.UpdateView):
    actions = ('add_to_page', 'remove_from_page')
    link_form_class = PagePromotionForm

    def get_context_data(self, *args, **kwargs):
        ctx = super(PromotionUpdateView, self).get_context_data(*args, **kwargs)
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
        return super(PromotionUpdateView, self).post(request, *args, **kwargs)

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


class PromotionUpdateRawHTMLView(PromotionUpdateView):
    template_name = 'dashboard/promotions/rawhtml_form.html'
    model = RawHTML
    form_class = RawHTMLForm


# ============
# DELETE VIEWS
# ============
        

class PromotionDeleteView(generic.DeleteView):
    template_name = 'dashboard/promotions/delete.html'

    def get_success_url(self):
        messages.info(self.request, "Promotion deleted successfully")
        return reverse('dashboard:promotion-list')


class PromotionDeleteRawHTMLView(PromotionDeleteView):
    model = RawHTML
