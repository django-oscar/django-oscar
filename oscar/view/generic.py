from django.http import HttpResponseBadRequest


class ModelView(object):
    u"""
    A generic view for models which can recieve GET and POST requests
    
    The __init__ method of subclasses should set the default response 
    variable.
    """
    template_file = None
    response = None
        
    def __call__(self, request, *args, **kwargs):
        
        self.request = request
        self.args = args
        self.kwargs = kwargs
        
        method_name = "handle_%s" % request.method.upper()
        model = self.get_model()
        try:
            getattr(self, method_name)(model)
        except AttributeError, e:
            return HttpResponseBadRequest("Unable to load model (%s)" % e)
        
        return self.response
        
    def handle_GET(self, model):
        u"""Default implementation of model view is to do nothing."""
        pass
    
    def handle_POST(self, model):
        u"""
        Handle a POST request to this resource.
        
        This will forward on request to a method of form "do_%s" where the
        second part needs to be specified as an "action" name within the
        request.
        
        If you don't want to handle POSTs this way, just override this method
        """
        if 'action' in self.request.POST:
            getattr(self, "do_%s" % self.request.POST['action'].lower())(model)
            
    def get_model(self):
        u"""Responsible for loading the model that is being acted on"""
        return None
