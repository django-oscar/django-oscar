from django.http import HttpResponseRedirect
from django.contrib import messages
from django.core.urlresolvers import reverse

from oscar.core.loading import import_module
import_module('checkout.utils', ['ProgressChecker'], locals())


def prev_steps_must_be_complete(view_fn):
    """
    Decorator for checking that previous steps of the checkout
    are complete.
    
    The completed steps (identified by URL-names) are stored in the session.
    If this fails, then we redirect to the next uncompleted step.
    """
    def _view_wrapper(self, request, *args, **kwargs):
        checker = ProgressChecker()
        if not checker.are_previous_steps_complete(request):
            messages.error(request, "You must complete this step of the checkout first")
            url_name = checker.get_next_step(request)
            return HttpResponseRedirect(reverse(url_name))
        return view_fn(self, request, *args, **kwargs)
    return _view_wrapper


def basket_required(view_fn):
    """
    Decorator for checking that the user has a non-empty basket
    or has a frozen one in the session
    """
    def _view_wrapper(self, request, *args, **kwargs):
        if request.basket.is_empty and not 'checkout_basket_id' in request.session:
            messages.error(request, "You must add some products to your basket before checking out")
            return HttpResponseRedirect(reverse('oscar-basket'))
        return view_fn(self, request, *args, **kwargs)
    return _view_wrapper


