import itertools

from django.views.generic import TemplateView, UpdateView, CreateView, DeleteView, FormView

from oscar.core.loading import get_classes

SingleProduct, RawHTML, Image, MultiImage = get_classes('promotions.models',
                                                        ['SingleProduct', 'RawHTML', 'Image', 'MultiImage'])


class PromotionListView(TemplateView):
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
        }
        return ctx
