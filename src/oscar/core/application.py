from django.apps import AppConfig
from django.core.exceptions import ImproperlyConfigured
from django.urls import reverse_lazy

from oscar.core.loading import feature_hidden


try:
    # Django 2
    from django.urls import URLPattern
except ImportError:
    # Django 1.11
    from django.urls.resolvers import RegexURLPattern as URLPattern


class OscarConfigMixin(object):
    """
    Base Oscar app configuration mixin, used to extend "django.apps.AppConfig"
    to in addition provide URL configurations and permissions.
    """
    # Instance namespace for the URLs
    namespace = None
    login_url = None

    #: A name that allows the functionality within this app to be disabled
    hidable_feature_name = None

    #: Maps view names to lists of permissions. We expect tuples of
    #: lists as dictionary values. A list is a set of permissions that all
    #: needto be fulfilled (AND). Only one set of permissions has to be
    #: fulfilled (OR).
    #: If there's only one set of permissions, as a shortcut, you can also
    #: just define one list.
    permissions_map = {}

    #: Default permission for any view not in permissions_map
    default_permissions = None

    def __init__(self, app_name, app_module, namespace=None, **kwargs):
        """
        kwargs:
            namespace: optionally specify the URL instance namespace
        """
        app_config_attrs = [
            'name',
            'module',
            'apps',
            'label',
            'verbose_name',
            'path',
            'models_module',
            'models',
        ]
        # To ensure sub classes do not add kwargs that are used by
        # "django.apps.AppConfig"
        clashing_kwargs = set(kwargs).intersection(app_config_attrs)
        if clashing_kwargs:
            raise ImproperlyConfigured(
                "Passed in kwargs can't be named the same as properties of "
                "AppConfig; clashing: %s." % ", ".join(clashing_kwargs))
        super().__init__(app_name, app_module)
        if namespace is not None:
            self.namespace = namespace
        # Set all kwargs as object attributes
        for key, value in kwargs.items():
            setattr(self, key, value)

    def get_urls(self):
        """
        Return the url patterns for this app.
        """
        return []

    def post_process_urls(self, urlpatterns):
        """
        Customise URL patterns.

        This method allows decorators to be wrapped around an apps URL
        patterns.

        By default, this only allows custom decorators to be specified, but you
        could override this method to do anything you want.

        Args:
            urlpatterns (list): A list of URL patterns

        """
        # Test if this the URLs in the Application instance should be
        # available.  If the feature is hidden then we don't include the URLs.
        if feature_hidden(self.hidable_feature_name):
            return []

        for pattern in urlpatterns:
            if hasattr(pattern, 'url_patterns'):
                self.post_process_urls(pattern.url_patterns)

            if isinstance(pattern, URLPattern):
                # Apply the custom view decorator (if any) set for this class if this
                # is a URL Pattern.
                decorator = self.get_url_decorator(pattern)
                if decorator:
                    pattern.callback = decorator(pattern.callback)

        return urlpatterns

    def get_permissions(self, url):
        """
        Return a list of permissions for a given URL name

        Args:
            url (str): A URL name (eg ``basket.basket``)

        Returns:
            list: A list of permission strings.
        """
        # url namespaced?
        if url is not None and ':' in url:
            view_name = url.split(':')[1]
        else:
            view_name = url
        return self.permissions_map.get(view_name, self.default_permissions)

    def get_url_decorator(self, pattern):
        """
        Return the appropriate decorator for the view function with the passed
        URL name. Mainly used for access-protecting views.

        It's possible to specify:

        - no permissions necessary: use None
        - a set of permissions: use a list
        - two set of permissions (`or`): use a two-tuple of lists

        See permissions_required decorator for details
        """
        from oscar.views.decorators import permissions_required
        permissions = self.get_permissions(pattern.name)
        if permissions:
            return permissions_required(permissions, login_url=self.login_url)

    @property
    def urls(self):
        # We set the application and instance namespace here
        return self.get_urls(), self.label, self.namespace


class OscarConfig(OscarConfigMixin, AppConfig):
    """
    Base Oscar app configuration.

    This is subclassed by each app to provide a customisable container for its
    configuration, URL configurations, and permissions.
    """


class OscarDashboardConfig(OscarConfig):
    login_url = reverse_lazy('dashboard:login')
