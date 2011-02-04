from django.conf import settings
from django.http import HttpResponse, Http404, HttpResponseRedirect
from django.template import Context, loader, RequestContext
from django.shortcuts import render_to_response, get_object_or_404
from django.core.urlresolvers import reverse

def class_based_view(class_obj):
    """
    Simple function that takes a view class and returns a function
    that instantiates a new instance each time it is called.
    
    This is used urls.py files when using class-based views.
    """
    def _instantiate_view_class(request, *args, **kwargs):
        return class_obj()(request, *args, **kwargs)
    return _instantiate_view_class


def home(request):
    """ 
    Oscar home page
    """
    return render_to_response('home.html', locals())
