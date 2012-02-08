import itertools

from django.views import generic
from django.core.urlresolvers import reverse

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


class PromotionCreateView(generic.CreateView):

    def get_success_url(self):
        return reverse('dashboard:promotions_list')


class PromotionCreateRawHTMLView(PromotionCreateView):
    template_name = 'dashboard/promotions/create_rawhtml.html'
    model = RawHTML
    form_class = RawHTMLForm

        

