import urlparse
from functools import wraps

from django.contrib.auth import REDIRECT_FIELD_NAME
from django.shortcuts import render
from django.contrib import messages
from django.contrib.auth.views import redirect_to_login
from django.core.exceptions import PermissionDenied
from django.core.urlresolvers import reverse_lazy
from django.utils.translation import ugettext_lazy as _


def staff_member_required(view_func, login_url=None):
    """
    Ensure that the user is a logged-in staff member.

    * If not authenticated, redirect to a specified login URL.
    * If not staff, show a 403 page

    This decorator is based on the decorator with the same name from
    django.contrib.admin.view.decorators.  This one is superior as it allows a
    redirect URL to be specified.
    """
    if login_url is None:
        login_url = reverse_lazy('customer:login')

    @wraps(view_func)
    def _checklogin(request, *args, **kwargs):
        if request.user.is_active and request.user.is_staff:
            return view_func(request, *args, **kwargs)

        # If user is not logged in, redirect to login page
        if not request.user.is_authenticated():
            # If the login url is the same scheme and net location then just
            # use the path as the "next" url.
            path = request.build_absolute_uri()
            login_scheme, login_netloc = urlparse.urlparse(login_url)[:2]
            current_scheme, current_netloc = urlparse.urlparse(path)[:2]
            if ((not login_scheme or login_scheme == current_scheme) and
                (not login_netloc or login_netloc == current_netloc)):
                path = request.get_full_path()

            messages.warning(request, _("You must log in to access this page"))
            return redirect_to_login(path, login_url, REDIRECT_FIELD_NAME)
        else:
            # User does not have permission to view this page
            raise PermissionDenied

    return _checklogin


def login_forbidden(view_func, template_name='login_forbidden.html',
                    status=403):
    """
    Only allow anonymous users to access this view.
    """
    @wraps(view_func)
    def _checklogin(request, *args, **kwargs):
        if not request.user.is_authenticated():
            return view_func(request, *args, **kwargs)
        return render(request, template_name, status=status)

    return _checklogin
