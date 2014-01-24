import six

from django.conf.urls import patterns

from oscar.core.loading import feature_hidden
from oscar.views.decorators import permissions_required


class Application(object):
    """
    Base application class.

    This is subclassed by each app to provide a customisable container for an
    app's views and permissions.
    """
    #: Namespace name
    name = None

    #: A name that allows the functionality within this app to be disabled
    hidable_feature_name = None

    #: Maps view names to a tuple or list of permissions
    permissions_map = {}

    #: Default permission for any view not in permissions_map
    default_permissions = None

    def __init__(self, app_name=None, **kwargs):
        self.app_name = app_name
        # Set all kwargs as object attributes
        for key, value in six.iteritems(kwargs):
            setattr(self, key, value)

    def get_urls(self):
        """
        Return the url patterns for this app.
        """
        return patterns('')

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
            return patterns('')

        for pattern in urlpatterns:
            if hasattr(pattern, 'url_patterns'):
                self.post_process_urls(pattern.url_patterns)
            if not hasattr(pattern, '_callback'):
                continue
            # Look for a custom decorator
            decorator = self.get_url_decorator(pattern)
            if decorator:
                # Nasty way of modifying a RegexURLPattern
                pattern._callback = decorator(pattern._callback)
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
        return permissions_required(permissions)

    @property
    def urls(self):
        # We set the application and instance namespace here
        return self.get_urls(), self.app_name, self.name
