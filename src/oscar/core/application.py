from django import VERSION as DJANGO_VERSION
from django.core.urlresolvers import RegexURLPattern, reverse_lazy

from oscar.core.loading import feature_hidden
from oscar.views.decorators import permissions_required


class Application(object):
    """
    Base application class.

    This is subclassed by each app to provide a customisable container for an
    app's views and permissions.
    """
    #: Application name
    name = None

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

    def __init__(self, app_name=None, **kwargs):
        """
        kwargs:
            app_name: optionally specify the instance namespace
        """
        self.app_name = app_name or self.name
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

            # In Django 1.8 and 1.9 we could distinguish the RegexURLPattern
            # by simply checking if the pattern has a `_callback` attribute.
            # In 1.10 this attribute is now only available as `callback`.
            # Since the `callback` attribute is also available on patterns we
            # should not modify (`RegexURLResolver`) we just do a isinstance()
            # check here.
            if DJANGO_VERSION < (1, 10):
                if not hasattr(pattern, '_callback'):
                    continue
                # Look for a custom decorator
                decorator = self.get_url_decorator(pattern)
                if decorator:
                    # Nasty way of modifying a RegexURLPattern
                    pattern._callback = decorator(pattern._callback)
            else:
                if isinstance(pattern, RegexURLPattern):
                    # Look for a custom decorator
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
        permissions = self.get_permissions(pattern.name)
        if permissions:
            return permissions_required(permissions, login_url=self.login_url)

    @property
    def urls(self):
        # We set the application and instance namespace here
        return self.get_urls(), self.name, self.app_name


class DashboardApplication(Application):
    login_url = reverse_lazy('dashboard:login')
