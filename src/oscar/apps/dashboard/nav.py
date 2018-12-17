import inspect
import logging
import sys
from collections import OrderedDict

from django.apps import apps
from django.core.exceptions import ImproperlyConfigured
from django.urls import NoReverseMatch, resolve, reverse

from oscar.core.application import OscarDashboardConfig
from oscar.core.exceptions import AppNotFoundError
from oscar.views.decorators import check_permissions

logger = logging.getLogger('oscar.dashboard')


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


def default_access_fn(user, url_name, url_args=None, url_kwargs=None):  # noqa C901 too complex
    """
    Given a url_name and a user, this function tries to assess whether the
    user has the right to access the URL.
    The application instance of the view is fetched via the Django app
    registry.
    Once the permissions for the view are known, the access logic used
    by the dashboard decorator is evaluated

    This function might seem costly, but a simple comparison with DTT
    did not show any change in response time
    """
    if url_name is None:  # it's a heading
        return True

    # get view module string.
    try:
        url = reverse(url_name, args=url_args, kwargs=url_kwargs)
    except NoReverseMatch:
        # In Oscar 1.5 this exception was silently ignored which made debugging
        # very difficult. Now it is being logged and in future the exception will
        # be propagated.
        logger.exception('Invalid URL name {}'.format(url_name))
        return False

    view_module = resolve(url).func.__module__

    # We can't assume that the view has the same parent module as the app
    # config, as either the app config or view can be customised. So we first
    # look it up in the app registry using "get_containing_app_config", and if
    # it isn't found, then we walk up the package tree, looking for an
    # OscarDashboardConfig class, from which we get an app label, and use that
    # to look it up again in the app registry using "get_app_config".
    app_config_instance = apps.get_containing_app_config(view_module)
    if app_config_instance is None:
        try:
            app_config_class = get_app_config_class(view_module)
        except AppNotFoundError:
            raise ImproperlyConfigured(
                "Please provide an OscarDashboardConfig subclass in the apps "
                "module or set a custom access_fn")
        if hasattr(app_config_class, 'label'):
            app_label = app_config_class.label
        else:
            app_label = app_config_class.name.rpartition('.')[2]
        try:
            app_config_instance = apps.get_app_config(app_label)
        except LookupError:
            raise AppNotFoundError(
                "Couldn't find an app with the label %s" % app_label)
        if not isinstance(app_config_instance, OscarDashboardConfig):
            raise AppNotFoundError(
                "Couldn't find an Oscar Dashboard app with the label %s" % app_label)

    # handle name-spaced view names
    if ':' in url_name:
        view_name = url_name.split(':')[1]
    else:
        view_name = url_name
    permissions = app_config_instance.get_permissions(view_name)
    return check_permissions(user, permissions)


def get_app_config_class(module_name):
    apps_module_name = module_name.rpartition('.')[0] + '.apps'
    if apps_module_name in sys.modules:
        oscar_dashboard_config_classes = []
        apps_module_classes = inspect.getmembers(sys.modules[apps_module_name], inspect.isclass)
        for klass in OrderedDict(apps_module_classes).values():
            if issubclass(klass, OscarDashboardConfig):
                oscar_dashboard_config_classes.append(klass)
        if oscar_dashboard_config_classes:
            return oscar_dashboard_config_classes[-1]
    raise AppNotFoundError(
        "Couldn't find an app to import %s from" % module_name)
