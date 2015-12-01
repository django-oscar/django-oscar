from functools import wraps

from django.contrib import messages
from django.contrib.auth import REDIRECT_FIELD_NAME
from django.contrib.auth.decorators import user_passes_test
from django.contrib.auth.views import redirect_to_login
from django.core.exceptions import PermissionDenied
from django.core.urlresolvers import reverse_lazy
from django.shortcuts import render
from django.utils.six.moves.urllib import parse
from django.utils.translation import ugettext_lazy as _


def staff_member_required(view_func, login_url=None):
    """
    Ensure that the user is a logged-in staff member.

    * If not authenticated, redirect to a specified login URL.
    * If not staff, show a 403 page

    This decorator is based on the decorator with the same name from
    django.contrib.admin.views.decorators.  This one is superior as it allows a
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
            login_scheme, login_netloc = parse.urlparse(login_url)[:2]
            current_scheme, current_netloc = parse.urlparse(path)[:2]
            if ((not login_scheme or login_scheme == current_scheme) and
                    (not login_netloc or login_netloc == current_netloc)):
                path = request.get_full_path()

            messages.warning(request, _("You must log in to access this page"))
            return redirect_to_login(path, login_url, REDIRECT_FIELD_NAME)
        else:
            # User does not have permission to view this page
            raise PermissionDenied

    return _checklogin


def check_permissions(user, permissions):
    """
    Permissions can be a list or a tuple of lists. If it is a tuple,
    every permission list will be evaluated and the outcome will be checked
    for truthiness.
    Each item of the list(s) must be either a valid Django permission name
    (model.codename) or a property or method on the User model
    (e.g. 'is_active', 'is_superuser').

    Example usage:
    - permissions_required(['is_staff', ])
      would replace staff_member_required
    - permissions_required(['is_anonymous', ])
      would replace login_forbidden
    - permissions_required((['is_staff',], ['partner.dashboard_access']))
      allows both staff users and users with the above permission
    """
    def _check_one_permission_list(perms):
        regular_permissions = [perm for perm in perms if '.' in perm]
        conditions = [perm for perm in perms if '.' not in perm]
        # always check for is_active if not checking for is_anonymous
        if (conditions and
                'is_anonymous' not in conditions and
                'is_active' not in conditions):
            conditions.append('is_active')
        attributes = [getattr(user, perm) for perm in conditions]
        # evaluates methods, explicitly casts properties to booleans
        passes_conditions = all([
            attr() if callable(attr) else bool(attr) for attr in attributes])
        return passes_conditions and user.has_perms(regular_permissions)

    if not permissions:
        return True
    elif isinstance(permissions, list):
        return _check_one_permission_list(permissions)
    else:
        return any(_check_one_permission_list(perm) for perm in permissions)


def permissions_required(permissions, login_url=None):
    """
    Decorator that checks if a user has the given permissions.
    Accepts a list or tuple of lists of permissions (see check_permissions
    documentation).

    If the user is not logged in and the test fails, she is redirected to a
    login page. If the user is logged in, she gets a HTTP 403 Permission Denied
    message, analogous to Django's permission_required decorator.
    """
    if login_url is None:
        login_url = reverse_lazy('customer:login')

    def _check_permissions(user):
        outcome = check_permissions(user, permissions)
        if not outcome and user.is_authenticated():
            raise PermissionDenied
        else:
            return outcome

    return user_passes_test(_check_permissions, login_url=login_url)


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
