from django.core.exceptions import ObjectDoesNotExist

from oscar.services import import_module

marketing_models = import_module('marketing.models', ['Banner'])


def banners(request):
    try:
        banner = marketing_models.Banner._default_manager.get(page_url=request.path)
        bindings = {'banner': banner}
    except ObjectDoesNotExist:
        bindings = {}
    return bindings

        
    