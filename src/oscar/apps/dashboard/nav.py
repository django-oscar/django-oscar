import re

from django.core.exceptions import ImproperlyConfigured
from django.core.urlresolvers import NoReverseMatch, resolve, reverse
from django.http import Http404

from oscar.core.loading import AppNotFoundError, get_class
from oscar.views.decorators import check_permissions


class Node(object):
    """
    A node in the dashboard navigation menu
    """

    def __init__(self, label, url_name=None, url_args=None, url_kwargs=None,
                 access_fn=None, icon=None):
        self.label = label
        self.icon = icon
        self.url_name = url_name
        self.url_args = url_args
        self.url_kwargs = url_kwargs
        self.access_fn = access_fn
        self.children = []

    @property
    def is_heading(self):
        return self.url_name is None

    @property
    def url(self):
        return reverse(self.url_name, args=self.url_args,
                       kwargs=self.url_kwargs)

    def add_child(self, node):
        self.children.append(node)

    def is_visible(self, user):
        return self.access_fn is None or self.access_fn(
            user, self.url_name, self.url_args, self.url_kwargs)

    def filter(self, user):
        if not self.is_visible(user):
            return None
        node = Node(
            label=self.label, url_name=self.url_name, url_args=self.url_args,
            url_kwargs=self.url_kwargs, access_fn=self.access_fn,
            icon=self.icon
        )
        for child in self.children:
            if child.is_visible(user):
                node.add_child(child)
        return node

    def has_children(self):
        return len(self.children) > 0


def default_access_fn(user, url_name, url_args=None, url_kwargs=None):
    """
    Given a url_name and a user, this function tries to assess whether the
    user has the right to access the URL.
    The application instance of the view is fetched via dynamic imports,
    and those assumptions will only hold true if the standard Oscar layout
    is followed.
    Once the permissions for the view are known, the access logic used
    by the dashboard decorator is evaluated

    This function might seem costly, but a simple comparison with DTT
    did not show any change in response time
    """
    exception = ImproperlyConfigured(
        "Please follow Oscar's default dashboard app layout or set a "
        "custom access_fn")
    if url_name is None:  # it's a heading
        return True
    # get view module string
    try:
        url = reverse(url_name, args=url_args, kwargs=url_kwargs)
        view_module = resolve(url).func.__module__
    except (NoReverseMatch, Http404):
        # if there's no match, no need to display it
        return False

    # We can't assume that the view has the same parent module as the app,
    # as either the app or view can be customised. So we turn the module
    # string (e.g. 'oscar.apps.dashboard.catalogue.views') into an app
    # label that can be loaded by get_class (e.g.
    # 'dashboard.catalogue.app), which then essentially checks
    # INSTALLED_APPS for the right module to load
    match = re.search('(dashboard[\w\.]*)\.views$', view_module)
    if not match:
        raise exception
    app_label_str = match.groups()[0] + '.app'

    try:
        app_instance = get_class(app_label_str, 'application')
    except AppNotFoundError:
        raise exception

    # handle name-spaced view names
    if ':' in url_name:
        view_name = url_name.split(':')[1]
    else:
        view_name = url_name
    permissions = app_instance.get_permissions(view_name)
    return check_permissions(user, permissions)
