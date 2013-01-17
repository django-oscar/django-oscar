from imp import new_module

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.db.models import get_model


class AppNotFoundError(Exception):
    pass


class ClassNotFoundError(Exception):
    pass


def get_class(module_label, classname):
    return get_classes(module_label, [classname])[0]


def get_classes(module_label, classnames):
    """
    Import classes that are found in a given module

    Usage:

        Product, Category = get_classes('catalogue.models', ['Product', 'Category'])

    This will look for the app in INSTALLED_APPS that matches 'catalogue'.  If
    you are not overriding Oscar's catalogue app, this will match
    'oscar.apps.catalogue' but if you are overriding, then it will match
    something like 'myproject.apps.catalogue'.

    It is smart enough to take some classes from the local module and some from
    Oscar's equivalent module if you choose to only override one.

    This is very similar to django.db.models.get_model although that is only
    for loading models while this method will load any class.
    """
    app_module_path = _get_app_module_path(module_label)
    if not app_module_path:
        raise AppNotFoundError("No app found matching '%s'" % module_label)

    # Check if app is in oscar
    if app_module_path.split('.')[0] == 'oscar':
        # Using core oscar class
        module_path = 'oscar.apps.%s' % module_label
        imported_module = __import__(module_path, fromlist=classnames)
        return _pluck_classes([imported_module], classnames)

    # App must be local - check if the requested module is in local app.  It
    # may not be as the local app may not override any classes in this module.
    app_label = module_label.split('.')[0]
    base_package = app_module_path.rsplit('.' + app_label, 1)[0]
    local_module_path = "%s.%s" % (base_package, module_label)
    try:
        imported_local_module = __import__(local_module_path,
                                           fromlist=classnames)
    except ImportError:
        # Module not in local app
        imported_local_module = {}

    # Attempt to import the classes form Oscar's core app too to patch any gaps
    oscar_module_path = "oscar.apps.%s" % module_label
    try:
        imported_oscar_module = __import__(oscar_module_path,
                                           fromlist=classnames)
    except ImportError:
        imported_modules = [imported_local_module]
    else:
        imported_modules = [imported_local_module, imported_oscar_module]

    return _pluck_classes(imported_modules, classnames)


def _pluck_classes(modules, classnames):
    """
    Build a list of classes taken from the passed list of modules
    """
    klasses = []
    for classname in classnames:
        klass = None
        for module in modules:
            if hasattr(module, classname):
                klass = getattr(module, classname)
                break
        if not klass:
            packages = [m.__name__ for m in modules]
            raise ClassNotFoundError("No class '%s' found in %s" % (
                classname, ", ".join(packages)))
        klasses.append(klass)
    return klasses


def _get_app_module_path(module_label):
    app_name = module_label.rsplit(".", 1)[0]
    for installed_app in settings.INSTALLED_APPS:
        if installed_app.endswith(app_name):
            return installed_app
    return None


def import_module(module_label, classes, namespace=None):
    """
    This is the deprecated old way of loading modules
    """
    klasses = get_classes(module_label, classes)
    if namespace:
        for classname, klass in zip(classes, klasses):
            namespace[classname] = klass
    else:
        module = new_module("oscar.apps.%s" % module_label)
        for classname, klass in zip(classes, klasses):
            setattr(module, classname, klass)
        return module


def get_profile_class():
    """
    Return the profile model class
    """
    app_label, model_name = settings.AUTH_PROFILE_MODULE.split('.')
    profile_class = get_model(app_label, model_name)
    if not profile_class:
        raise ImproperlyConfigured("Can't import profile model")
    return profile_class
