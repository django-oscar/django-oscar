
def class_based_view(class_obj):
    u"""
    Decorates a view class and returns a function
    that instantiates a new instance each time it is called.
    
    This is supposed to be used within urls.py files when using class-based views.
    """
    def _instantiate_view_class(request, *args, **kwargs):
        return class_obj()(request, *args, **kwargs)
    return _instantiate_view_class
