from django.conf.urls.defaults import patterns


class Application(object):
    name = None
    
    def __init__(self, app_name=None, **kwargs):
        self.app_name = app_name
        # Set all kwargs as object attributes
        for key, value in kwargs.iteritems():
            setattr(self, key, value)
    
    def get_urls(self):
        """
        Return the url patterns for this app, MUST be implemented in the subclass
        """
        return patterns('')
    
    @property
    def urls(self):
        # We set the application and instance namespace here
        return self.get_urls(), self.app_name, self.name