from django.apps import AppConfig, apps
from django.core.exceptions import ImproperlyConfigured
from django.urls import URLPattern, include, path, re_path, reverse_lazy


class AutoLoadURLsConfigMixin:
    include_urls_in_parent = True

    def get_app_label_url_endpoint_mapping(self):
        """
        Return dict with `app_label` as key and value as either:
            1. String representing the endpoint of app's URL configurations. Example,
                >>> {"reviews":"reviews/"}
            2. Dict with configurations of how the app's URL endpoint(s) will be generated. Example,
                >>> # Generate endpoint by processing it's kwargs using regex.
                >>> {"reviews":{"endpoint":"^(?P<product_slug>[\\w-]*)_(?P<product_pk>\\d+)/reviews/","regex":True}}
        """
        return {}

    def _create_required_attributes(self):
        for label in self.get_app_label_url_endpoint_mapping():
            try:
                app_config = apps.get_app_config(label)
            except LookupError:
                app_config = None
            setattr(self, f'{label}_app', app_config)

    def ready(self):
        self._create_required_attributes()

    def get_auto_loaded_urls(self):
        urls, count = [], 0
        for label, value in self.get_app_label_url_endpoint_mapping().items():
            app_config_attribute_name = f'{label}_app'
            if count == 0 and not hasattr(self, app_config_attribute_name):
                # this method was probably called before calling `self._create_required_attributes()`
                self._create_required_attributes()
            count += 1

            endpoint, regex = value, False
            if isinstance(value, dict):
                endpoint = value.get('endpoint') or ''
                regex = value.get('regex', False)

            app_config = getattr(self, app_config_attribute_name)
            if app_config is None:
                continue  # app with the label probably wasn't installed

            child_app_urls = app_config.urls
            if app_config.include_urls_in_parent:
                child_app_urls = include((app_config.get_urls(), app_config.namespace))

            urls.append(re_path(endpoint, child_app_urls) if regex else path(endpoint, child_app_urls))
        return urls


class OscarConfigMixin(object):
    """
    Base Oscar app configuration mixin, used to extend :py:class:`django.apps.AppConfig`
    to also provide URL configurations and permissions.
    """
    # Instance namespace for the URLs
    namespace = None
    login_url = None

    #: Maps view names to lists of permissions. We expect tuples of
    #: lists as dictionary values. A list is a set of permissions that all
    #: need to be fulfilled (AND). Only one set of permissions has to be
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
        # :py:class:`django.apps.AppConfig`
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
        Return the URL patterns for this app.
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
            url (str): A URL name (e.g., ``basket.basket``)

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


class OscarConfig(AutoLoadURLsConfigMixin, OscarConfigMixin, AppConfig):
    """
    Base Oscar app configuration.

    This is subclassed by each app to provide a customisable container for its
    configuration, URL configurations, and permissions.
    """


class OscarDashboardConfig(OscarConfig):
    login_url = reverse_lazy('dashboard:login')
