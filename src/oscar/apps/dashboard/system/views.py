from django import forms
from django.conf import settings
from django.core.cache import cache
from django.urls import reverse
from django.views import generic

from oscar.core.loading import get_model

Configuration = get_model('system', 'Configuration')


class ConfigForm(forms.ModelForm):
    class Meta:
        model = Configuration
        fields = '__all__'


class ConfigUpdateView(generic.UpdateView):
    model = Configuration
    form_class = ConfigForm
    template_name = 'dashboard/system/config_update.html'
    
    def get_success_url(self):
        return reverse('dashboard:system-config')
    
    def get_object(self, queryset=None):
        obj = Configuration.objects.first()
        if obj is None:
            obj = Configuration(
                shop_name=settings.OSCAR_SHOP_NAME,
                shop_tagline=settings.OSCAR_SHOP_TAGLINE,
                homepage_url=settings.OSCAR_HOMEPAGE,
                # Fallback to old settings name for backwards compatibility
                use_less=(
                    getattr(settings, 'OSCAR_USE_LESS', None) or
                    getattr(settings, 'USE_LESS', False)
                ),
                google_analytics_id=(
                    getattr(settings, 'OSCAR_GOOGLE_ANALYTICS_ID', None) or
                    getattr(settings, 'GOOGLE_ANALYTICS_ID', None)
                )
            )

        return obj
    
    def form_valid(self, form):
        """
        Clear system config cache on save
        """
        cache.delete('system-config')
        return super().form_valid(form)
        
