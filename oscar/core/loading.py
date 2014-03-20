import sys
import traceback
from importlib import import_module

from django.conf import settings
from django.db.models import get_model as django_get_model
from django.utils import six as django_six

from oscar.core.exceptions import (ModuleNotFoundError, ClassNotFoundError,
                                   AppNotFoundError)


def import_string(dotted_path):
    """
    Import a dotted module path and return the attribute/class designated by
    the last name in the path. Raise ImportError if the import failed.

    This is backported from unreleased Django 1.7 at
    47927eb786f432cb069f0b00fd810c465a78fd71. Can be removed once we don't
    support Django versions below 1.7.
    """
    try:
        module_path, class_name = dotted_path.rsplit('.', 1)
    except ValueError:
        msg = "%s doesn't look like a module path" % dotted_path
        django_six.reraise(ImportError, ImportError(msg), sys.exc_info()[2])

    module = import_module(module_path)

    try:
        return getattr(module, class_name)
    except AttributeError:
        msg = 'Module "%s" does not define a "%s" attribute/class' % (
            dotted_path, class_name)
        django_six.reraise(ImportError, ImportError(msg), sys.exc_info()[2])
    try:
        module_path, class_name = dotted_path.rsplit('.', 1)
    except ValueError:
        msg = "%s doesn't look like a module path" % dotted_path
        django_six.reraise(ImportError, ImportError(msg), sys.exc_info()[2])

    module = __import__(module_path, fromlist=[class_name])

    try:
        return getattr(module, class_name)
    except AttributeError:
        msg = 'Module "%s" does not define a "%s" attribute/class' % (
            dotted_path, class_name)
        django_six.reraise(ImportError, ImportError(msg), sys.exc_info()[2])


def get_class(module_label, classname):
    """
    Dynamically import a single class from the given module.

    This is a simple wrapper around `get_classes` for the case of loading a
    single class.

    Args:
        module_label (str): Module label comprising the app label and the
            module name, separated by a dot.  For example, 'catalogue.forms'.
        classname (str): Name of the class to be imported.

    Returns:
        The requested class object or `None` if it can't be found
    """
    return get_classes(module_label, [classname])[0]


def get_classes(module_label, classnames):
    """
    Dynamically import a list of classes from the given module.

    This works by looping over ``INSTALLED_APPS`` and looking for a match
    against the passed module label.  If the requested class can't be found in
    the matching module, then we attempt to import it from the corresponding
    core Oscar app (assuming the matched module isn't in Oscar).

    This is very similar to ``django.db.models.get_model`` function for
    dynamically loading models.  This function is more general though as it can
    load any class from the matching app, not just a model.

    Args:
        module_label (str): Module label comprising the app label and the
            module name, separated by a dot.  For example, 'catalogue.forms'.
        classname (str): Name of the class to be imported.

    Returns:
        The requested class object or ``None`` if it can't be found

    Examples:

        Load a single class:

        >>> get_class('dashboard.catalogue.forms', 'ProductForm')
        oscar.apps.dashboard.catalogue.forms.ProductForm

        Load a list of classes:

        >>> get_classes('dashboard.catalogue.forms',
        ...             ['ProductForm', 'StockRecordForm'])
        [oscar.apps.dashboard.catalogue.forms.ProductForm,
         oscar.apps.dashboard.catalogue.forms.StockRecordForm]

    Raises:

        AppNotFoundError: If no app is found in ``INSTALLED_APPS`` that matches
            the passed module label.

        ImportError: If the attempted import of a class raises an
            ``ImportError``, it is re-raised
    """

    # import from Oscar package (should succeed in most cases)
    # e.g. 'oscar.apps.dashboard.catalogue.forms'
    oscar_module_label = "oscar.apps.%s" % module_label
    oscar_module = _import_module(oscar_module_label, classnames)

    # Split module_label into the section that we expect to find in
    # INSTALLED_APPS (package) and the rest (module)
    # e.g. split 'dashboard.catalogue.forms' in 'dashboard.catalogue', 'forms'
    # It is assumed that any imported module is only ever one level below
    # package, e.g. 'dashboard.catalogue.forms.widgets' will break
    if '.' in module_label:
        package, module = module_label.rsplit('.', 1)
    else:
        # Importing from top-level modules is not supported, e.g.
        # get_class('shipping', 'Scale'). That should be easy to fix,
        # but @maikhoepfel had a stab and could not get it working reliably.
        # Overridable classes in a __init__.py might not be a good idea anyway.
        raise ValueError(
            "Importing from top-level modules is not supported")

    # returns e.g. 'oscar.apps.dashboard.catalogue',
    # 'yourproject.apps.dashboard.catalogue' or 'dashboard.catalogue'
    installed_apps_entry = _get_installed_apps_entry(package)
    if installed_apps_entry.startswith('oscar.apps.'):
        # The entry is obviously an Oscar one, we don't import again
        local_module = None
    else:
        # Attempt to import the classes from the local module
        # e.g. 'yourproject.dashboard.catalogue.forms'
        local_module_label = installed_apps_entry + '.' + module
        local_module = _import_module(local_module_label, classnames)

    if oscar_module is local_module is None:
        # This intentionally doesn't raise an ImportError, because that could
        # get masked in some circular import scenarios.
        raise ModuleNotFoundError(
            "The module with label '%s' could not be imported. This either"
            "means that it indeed does not exist, or you might have a problem"
            " with a circular import." % module_label
        )

    # return imported classes, giving preference to ones from the local package
    return _pluck_classes([local_module, oscar_module], classnames)


def _import_module(module_label, classnames):
    """
    Imports the module with the given name.
    Returns None if the module doesn't exist, but propagates any import errors.
    """
    try:
        return __import__(module_label, fromlist=classnames)
    except ImportError:
        # There are 2 reasons why there could be an ImportError:
        #
        #  1. Module does not exist. In that case, we ignore the import and
        #     return None
        #  2. Module exists but another ImportError occurred when trying to
        #     import the module. In that case, it is important to propagate the
        #     error.
        #
        # ImportError does not provide easy way to distinguish those two cases.
        # Fortunately, the traceback of the ImportError starts at __import__
        # statement. If the traceback has more than one frame, it means that
        # application was found and ImportError originates within the local app
        __, __, exc_traceback = sys.exc_info()
        frames = traceback.extract_tb(exc_traceback)
        if len(frames) > 1:
            raise


def _pluck_classes(modules, classnames):
    """
    Gets a list of class names and a list of modules to pick from.
    For each class name, will return the class from the first module that has a
    matching class.
    """
    klasses = []
    for classname in classnames:
        klass = None
        for module in modules:
            if hasattr(module, classname):
                klass = getattr(module, classname)
                break
        if not klass:
            packages = [m.__name__ for m in modules if m is not None]
            raise ClassNotFoundError("No class '%s' found in %s" % (
                classname, ", ".join(packages)))
        klasses.append(klass)
    return klasses


def _get_installed_apps_entry(app_name):
    """
    Walk through INSTALLED_APPS and return the first match. This does depend
    on the order of INSTALLED_APPS and will break if e.g. 'dashboard.catalogue'
    comes before 'catalogue' in INSTALLED_APPS.
    """
    for installed_app in settings.INSTALLED_APPS:
        if installed_app.endswith(app_name):
            return installed_app
    raise AppNotFoundError("No app found matching '%s'" % app_name)


def get_profile_class():
    """
    Return the profile model class
    """
    # The AUTH_PROFILE_MODULE setting was deprecated in Django 1.5, but it
    # makes sense for Oscar to continue to use it. Projects built on Django
    # 1.4 are likely to have used a profile class and it's very difficult to
    # upgrade to a single user model. Hence, we should continue to support
    # having a separate profile class even if Django doesn't.
    setting = getattr(settings, 'AUTH_PROFILE_MODULE', None)
    if setting is None:
        return None
    app_label, model_name = settings.AUTH_PROFILE_MODULE.split('.')
    return get_model(app_label, model_name)


def feature_hidden(feature_name):
    """
    Test if a certain Oscar feature is disabled.
    """
    return (feature_name is not None and
            feature_name in settings.OSCAR_HIDDEN_FEATURES)


def get_model(app_label, model_name, *args, **kwargs):
    """
    Gets a model class by it's app label and model name. Fails loudly if the
    model class can't be imported.
    This is merely a thin wrapper around Django's get_model function.
    """
    model = django_get_model(app_label, model_name, *args, **kwargs)
    if model is None:
        raise ImportError(
            "{app_label}.{model_name} could not be imported.".format(
                app_label=app_label, model_name=model_name))
    return model
