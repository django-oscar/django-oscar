from exceptions import Exception
from imp import new_module

from django.conf import settings

class AppNotFoundError(Exception):
    pass

def import_module(module_label, classes=[]):
    u"""
    For dynamically importing classes from a module based on the mapping within 
    settings.py
    
    Eg. calling import_module('product.models') will search INSTALLED_APPS for
    the relevant product app (default is 'oscar.product') and then import the
    classes from there.  If the class can't be found in the overriding module, 
    then we attempt to import it from within oscar.  
    
    We search the INSTALLED_APPS list to find the appropriate app string and 
    import that.
    
    This is very similar to django.db.models.get_model although that is only 
    for loading models while this method will load any class.
    """
    # Classes must be specified in order for __import__ to work correctly.  It's
    # also a good practice
    if not classes:
        raise ValueError("You must specify the classes to import")
    
    # Arguments will be things like 'product.models' and so we
    # we take the first component to find within the INSTALLED_APPS list.
    app_name = module_label.split(".")[0]
    for installed_app in settings.INSTALLED_APPS:
        installed_app_parts = installed_app.split(".")
        try: 
            # We search the second component of the installed apps
            if app_name == installed_app_parts[1]:
                if installed_app_parts[0] == 'oscar':
                    # Using core module explicitly
                    return _import_classes_from_module("oscar.%s" % module_label, classes)
                else:
                    # Using local override - check that requested module exists
                    local_module_name = "%s.%s" % (installed_app_parts[0], module_label)
                    try:
                        imported_local_mod = __import__(local_module_name, fromlist=classes)
                    except ImportError, e:
                        # Module doesn't exist, fall back to oscar core
                        return _import_classes_from_module("oscar.%s" % module_label, classes)
                    
                    module = new_module(local_module_name)
                    imported_oscar_mod = __import__("oscar.%s" % module_label, fromlist=classes)
                    for classname in classes:
                        if hasattr(imported_local_mod, classname):
                            module.__setattr__(classname, getattr(imported_local_mod, classname))
                        else:
                            module.__setattr__(classname, getattr(imported_oscar_mod, classname))
                return module
        except IndexError:
            pass
    raise AppNotFoundError("Unable to find an app matching %s in INSTALLED_APPS" % (app_name,))
    
def _import_classes_from_module(module_name, classes):
    module = new_module(module_name)   
    imported_module = __import__(module_name, fromlist=classes)
    for classname in classes:
        module.__setattr__(classname, getattr(imported_module, classname)) 
    return module
