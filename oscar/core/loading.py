from imp import new_module

from django.conf import settings


class AppNotFoundError(Exception):
    pass


def import_module(module_label, classes, namespace=None):
    u"""
    For dynamically importing classes from a module.
    
    Eg. calling import_module('catalogue.models') will search INSTALLED_APPS for
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
    
    # Arguments will be things like 'catalogue.models' and so we
    # we take the first component to find within the INSTALLED_APPS list.
    app_name = module_label.rsplit(".", 1)[0] 
    for installed_app in settings.INSTALLED_APPS:
        base_package = installed_app.split(".")[0]
        module_name = installed_app.split(".", 2).pop() # strip oscar.apps
        try: 
            # We search the second component of the installed apps
            if app_name == module_name:
                if base_package == 'oscar':
                    # Using core module explicitly
                    return _import_classes_from_module("oscar.apps.%s" % module_label, classes, namespace)
                else:
                    # Using local override - check that requested module exists
                    local_app = "%s.%s" % (base_package, module_label)
                    try:
                        imported_local_mod = __import__(local_app, fromlist=classes)
                    except ImportError, e:
                        # Module doesn't exist, fall back to oscar core.  This can be tricky
                        # as if the overriding module has an import error, it will get picked up
                        # here.
                        if str(e).startswith("No module named"):
                            return _import_classes_from_module("oscar.apps.%s" % module_label, classes, namespace)
                        raise e
                    
                    # Found overriding module, merging custom classes with core
                    module = new_module(local_app)
                    imported_oscar_mod = __import__("oscar.apps.%s" % module_label, fromlist=classes)
                    for classname in classes:
                        if hasattr(imported_local_mod, classname):
                            if namespace:
                                namespace[classname] = getattr(imported_local_mod, classname)
                            else:
                                module.__setattr__(classname, getattr(imported_local_mod, classname))
                        else:
                            if namespace:
                                namespace[classname] = getattr(imported_oscar_mod, classname)
                            else:
                                module.__setattr__(classname, getattr(imported_oscar_mod, classname))
                return module
        except IndexError:
            pass
    raise AppNotFoundError("Unable to find an app matching %s in INSTALLED_APPS" % (app_name,))
    
    
def _import_classes_from_module(module_name, classes, namespace):
    imported_module = __import__(module_name, fromlist=classes)
    if namespace:
        for classname in classes:
            namespace[classname] = getattr(imported_module, classname)
        return 
    
    module = new_module(module_name)   
    for classname in classes:
        setattr(module, classname, getattr(imported_module, classname))
    return module
