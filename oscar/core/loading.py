import sys
import traceback

from django.conf import settings
from django.db.models import get_model as django_get_model

from oscar.core.exceptions import (ModuleNotFoundError, ClassNotFoundError,
                                   AppNotFoundError)


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

    # e.g. split 'dashboard.catalogue.forms' in 'dashboard.catalogue', 'forms'
    package, module = module_label.rsplit('.', 1)

    # import from Oscar package (should succeed in most cases)
    # e.g. 'oscar.apps.dashboard.catalogue.forms'
    oscar_module_label = "oscar.apps.%s" % module_label
    oscar_module = _import_oscar_module(oscar_module_label, classnames)

    # returns e.g. 'oscar.apps.dashboard.catalogue',
    # 'yourproject.apps.dashboard.catalogue' or 'dashboard.catalogue'
    installed_apps_entry = _get_installed_apps_entry(package)
    if not installed_apps_entry.startswith('oscar.apps.'):
        # Attempt to import the classes from the local module
        # e.g. 'yourproject.dashboard.catalogue.forms'
        local_module_label = installed_apps_entry + '.' + module
        local_module = _import_local_module(local_module_label, classnames)
    else:
        # The entry is obviously an Oscar one, we don't import again
        local_module = None

    if oscar_module is local_module is None:
        # This intentionally doesn't rise an ImportError, because it would get
        # masked by in some circular import scenarios.
        raise ModuleNotFoundError(
            "The module with label '%s' could not be imported. This either"
            "means that it indeed does not exist, or you might have a problem"
            " with a circular import." % module_label
        )

    # return imported classes, giving preference to ones from the local package
    return _pluck_classes([local_module, oscar_module], classnames)


def _import_local_module(local_module_label, classnames):
    try:
        return __import__(local_module_label, fromlist=classnames)
    except ImportError:
        # There are 2 reasons why there is ImportError:
        #  1. local_app does not exist
        #  2. local_app exists but is corrupted (ImportError inside of the app)
        #
        # Obviously, for the reason #1 we want to fall back to use Oscar app.
        # For the reason #2 we want to propagate error (the dev obviously wants
        # to override app and not use Oscar app)
        #
        # ImportError does not provide easy way to distinguish those two cases.
        # Fortunately, the traceback of the ImportError starts at __import__
        # statement. If the traceback has more than one frame, it means that
        # application was found and ImportError originates within the local app
        __, __, exc_traceback = sys.exc_info()
        frames = traceback.extract_tb(exc_traceback)
        if len(frames) > 1:
            raise


def _import_oscar_module(oscar_module_label, classnames):
    try:
        return __import__(oscar_module_label, fromlist=classnames)
    except ImportError:
        # Oscar does not have this application, can't fallback to it
        return None


def _pluck_classes(modules, classnames):
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
