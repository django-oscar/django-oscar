import itertools

from django.views import generic
from django.core.urlresolvers import reverse
from django.contrib import messages

from oscar.core.loading import get_classes, get_class

SingleProduct, RawHTML, Image, MultiImage = get_classes('promotions.models',
    ['SingleProduct', 'RawHTML', 'Image', 'MultiImage'])
SelectForm, RawHTMLForm = get_classes('dashboard.promotions.forms', 
    ['PromotionTypeSelectForm', 'RawHTMLForm'])


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


# ============
# CREATE VIEWS
# ============

class PromotionCreateView(generic.CreateView):

    def get_success_url(self):
        messages.info(self.request, "Promotion created successfully")
        return reverse('dashboard:promotion-list')


class PromotionCreateRawHTMLView(PromotionCreateView):
    template_name = 'dashboard/promotions/create_rawhtml.html'
    model = RawHTML
    form_class = RawHTMLForm


# ============
# UPDATE VIEWS
# ============
        

class PromotionUpdateView(generic.UpdateView):

    def get_success_url(self):
        messages.info(self.request, "Promotion updated successfully")
        return reverse('dashboard:promotion-list')


class PromotionUpdateRawHTMLView(PromotionUpdateView):
    template_name = 'dashboard/promotions/create_rawhtml.html'
    model = RawHTML
    form_class = RawHTMLForm

