import re
from django.core.urlresolvers import reverse, resolve, NoReverseMatch
from django.core.exceptions import ImproperlyConfigured
from django.conf import settings
from django.http import Http404
from oscar.core.loading import get_class, AppNotFoundError
from oscar.views.decorators import check_permissions


class Node(object):

    def __init__(self, label, url_name=None, url_args=None, url_kwargs=None,
                 access_fn=None, icon=None):
        self.label = label
        self.icon = icon
        self.url_name = url_name
        self.url_args = url_args
        self.url_kwargs = url_kwargs
        self.access_fn = access_fn or self._default_access_fn
        self.children = []

    @property
    def is_heading(self):
        return self.url_name is None

    @property
    def url(self):
        return reverse(self.url_name, args=self.url_args,
                       kwargs=self.url_kwargs)

    def _default_access_fn(self, user):
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
        if self.is_heading:
            return True
        # get view module string
        try:
            url = reverse(self.url_name, args=self.url_args,
                          kwargs=self.url_kwargs)
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
        if ':' in self.url_name:
            view_name = self.url_name.split(':')[1]
        else:
            view_name = self.url_name
        permissions = app_instance.get_permissions(view_name)
        return check_permissions(user, permissions)

    def add_child(self, node):
        self.children.append(node)

    def is_visible(self, user):
        return self.access_fn is None or self.access_fn(user)

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


def get_nodes(user):
    """
    Return the visible navigation nodes for the passed user
    """
    all_nodes = create_menu(settings.OSCAR_DASHBOARD_NAVIGATION)
    visible_nodes = []
    for node in all_nodes:
        filtered_node = node.filter(user)
        # don't append headings without children
        if filtered_node and (
                filtered_node.has_children() or not filtered_node.is_heading):
            visible_nodes.append(filtered_node)
    return visible_nodes


def create_menu(menu_items, parent=None):
    """
    Create the navigation nodes based on a passed list of dicts
    """
    nodes = []
    for menu_dict in menu_items:
        try:
            label = menu_dict['label']
        except KeyError:
            raise ImproperlyConfigured(
                "No label specified for menu item in dashboard")

        children = menu_dict.get('children', [])
        if children:
            node = Node(label=label, icon=menu_dict.get('icon', None),
                        access_fn=menu_dict.get('access_fn', None))
            create_menu(children, parent=node)
        else:
            node = Node(label=label, icon=menu_dict.get('icon', None),
                        url_name=menu_dict.get('url_name', None),
                        url_kwargs=menu_dict.get('url_kwargs', None),
                        url_args=menu_dict.get('url_args', None),
                        access_fn=menu_dict.get('access_fn', None))
        if parent is None:
            nodes.append(node)
        else:
            parent.add_child(node)
    return nodes
