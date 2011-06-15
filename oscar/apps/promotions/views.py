from django.http import HttpResponseRedirect
from django.views.generic import TemplateView, RedirectView
from django.core.urlresolvers import reverse


class HomeView(TemplateView):
    template_name = 'promotions/home.html'


class RecordClickView(RedirectView):
    
    model=None
    
    def get_redirect_url(self, **kwargs):
        try:
            prom = self.model.objects.get(pk=kwargs['pk'])
        except self.model.DoesNotExist:
            return reverse('promotions:home')  

        if prom.promotion.has_link:
            prom.record_click()
            return prom.link_url
        return reverse('promotions:home')

