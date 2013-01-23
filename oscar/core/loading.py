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
    Import the specified classes given a module label

    This function provides a mechanism to override functionality provided by
    3rd party apps (such as Oscar) by creating apps with the same app label.
    It allows classes to be dynamically imported from such overridig apps but
    falling back to a 'default package' if no matching classes are found.

    Sample usage:

        OrderCreator = get_classes('order.utils', ['OrderCreator'])

    Here 'order.utils' is the module label, comprising an app label 'order' and
    a module name 'utils'.  We loop over INSTALLED_APPS looking for an app
    with label 'order'.

    * If this is in the default package (eg the app is 'oscar.apps.order') we
      simply import the classes from 'oscar.apps.order.utils'.

    * If not, then there is an overriding app that we must consider first (eg
      'myproject.apps.order').  We look for a utils module within this app and
      attemp to import the classes from there.  Additionally, we import the
      classes from the default package 'oscar.apps.order to patch any gaps.
      The classes from in the overriding module take precedence.

    This is very similar to django.db.models.get_model although that is only
    for loading models while this method will load any class.
    """
    import_paths = ["%s.%s" % (root_package_name, module_label)
                    for root_package_name in settings.ROOT_PACKAGES]
    imported_modules = [try_to_import(path, fromlist=classnames)
                        for path in import_paths]
    imported_modules = [module for module in imported_modules if module]
    return _pluck_classes(imported_modules, classnames)


def try_to_import(module_path, **kwargs):
    try:
        return __import__(module_path, **kwargs)
    except ImportError:
        return None


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
