from django.conf import settings
from django.http import HttpResponse, Http404, HttpResponseRedirect
from django.template import Context, loader, RequestContext
from django.shortcuts import render_to_response, get_object_or_404
from django.core.urlresolvers import reverse


def home(request):
    """ 
    Oscar home page
    """
    return render_to_response('home.html', locals())
