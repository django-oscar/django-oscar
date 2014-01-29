import sys
import traceback

from django.conf import settings
from django.db.models import get_model as django_get_model


class AppNotFoundError(Exception):
    pass


class ClassNotFoundError(Exception):
    pass


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
    Dynamically import a list of  classes from the given module.

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

        >>> get_class('basket.forms', 'BasketLineForm')
        oscar.apps.basket.forms.BasketLineForm

        Load a list of classes:

        >>> get_classes('basket.forms', ['BasketLineForm', 'AddToBasketForm'])
        [oscar.apps.basket.forms.BasketLineForm,
         oscar.apps.basket.forms.AddToBasketForm]

    Raises:

        AppNotFoundError: If no app is found in ``INSTALLED_APPS`` that matches
            the passed module label.

        ImportError: If the attempted import of a class raises an
            ``ImportError``, it is re-raised
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
    if '.' in app_module_path:
        base_package = app_module_path.rsplit('.' + app_label, 1)[0]
        local_app = "%s.%s" % (base_package, module_label)
    else:
        local_app = module_label
    try:
        imported_local_module = __import__(local_app, fromlist=classnames)
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

        # Module not in local app
        imported_local_module = {}
    oscar_app = "oscar.apps.%s" % module_label
    try:
        imported_oscar_module = __import__(oscar_app, fromlist=classnames)
    except ImportError:
        # Oscar does not have this application, can't fallback to it
        imported_oscar_module = None

    return _pluck_classes([imported_local_module, imported_oscar_module],
                          classnames)


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
