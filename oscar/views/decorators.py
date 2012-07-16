import urlparse
from functools import wraps

from django.contrib.auth import REDIRECT_FIELD_NAME
from django.contrib import messages
from django.utils.translation import ugettext_lazy as _


def staff_member_required(view_func, login_url='/accounts/login/'):
    """
    Decorator for views that checks that the user is logged in and is a staff
    member. The user is redirected to the login page specified by *login_url*
    if not authenticated.

    This decorator is based on the admin decorator provided by the the django
    ``auth`` and ``admin`` packages.
    """
    @wraps(view_func)
    def _checklogin(request, *args, **kwargs):
        if request.user.is_active and request.user.is_staff:
            return view_func(request, *args, **kwargs)

        # If the login url is the same scheme and net location then just
        # use the path as the "next" url.
        path = request.build_absolute_uri()
        login_scheme, login_netloc = urlparse.urlparse(login_url)[:2]
        current_scheme, current_netloc = urlparse.urlparse(path)[:2]
        if ((not login_scheme or login_scheme == current_scheme) and
            (not login_netloc or login_netloc == current_netloc)):
            path = request.get_full_path()

        messages.warning(request, _("You must log in to access this page"))

        from django.contrib.auth.views import redirect_to_login
        return redirect_to_login(path, login_url, REDIRECT_FIELD_NAME)

    return _checklogin
