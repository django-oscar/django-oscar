class Application(object):
    name = None
    
    def __init__(self, app_name=None, **kwargs):
        self.app_name = app_name
        for key, value in kwargs.iteritems():
            setattr(self, key, value)
    
    def get_urls(self):
        u"""
        Return the url patterns for this app, MUST be implemented in the subclass
        """
        pass
    
    @property
    def urls(self):
        return self.get_urls(), self.app_name, self.name