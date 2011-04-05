from django.core.exceptions import ObjectDoesNotExist

from oscar.services import import_module

marketing_models = import_module('marketing.models', ['Banner', 'Pod'])


def marketing(request):
    u"""
    For adding bindings for banners and pods to the template
    context.
    """
    bindings = {
        'url_path': request.path
    }
    
    # Look for a banner
    try:
        banner = marketing_models.Banner._default_manager.get(page_url=request.path)
        bindings['banner'] = banner
    except ObjectDoesNotExist:
        pass
    
    # Looks for pods
    try:
        pods = marketing_models.Pod._default_manager.filter(page_url=request.path)
        bindings['pods'] = pods
    except ObjectDoesNotExist:
        pass

    return bindings

        
    