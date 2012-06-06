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
    For dynamically importing classes from a module.

    Eg. calling get_classes('catalogue.models', ['Product']) will search
    INSTALLED_APPS for the relevant product app (default is
    'oscar.apps.catalogue') and then import the classes from there.  If the
    class can't be found in the overriding module, then we attempt to import it
    from within oscar.

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

    # App must be local - check if module is in local app (it could be in
    # oscar's)
    app_label = module_label.split('.')[0]
    base_package = app_module_path.rsplit('.'+app_label, 1)[0]
    local_app = "%s.%s" % (base_package, module_label)
    try:
        imported_local_module = __import__(local_app, fromlist=classnames)
    except ImportError:
        # Module not in local app
        imported_local_module = {}
    oscar_app = "oscar.apps.%s" % module_label
    imported_oscar_module = __import__(oscar_app, fromlist=classnames)

    return _pluck_classes([imported_local_module, imported_oscar_module], classnames)


def _pluck_classes(modules, classnames):
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
