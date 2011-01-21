from django.conf import settings
from django.http import HttpResponse, Http404, HttpResponseRedirect
from django.template import Context, loader, RequestContext
from django.shortcuts import render_to_response, get_object_or_404
from django.core.urlresolvers import reverse

def add(request):
    """ 
    Pages should POST to this view to add an item to someone's basket
    """
    return HttpResponseRedirect('/shop/')
