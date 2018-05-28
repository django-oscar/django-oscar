from django.core import exceptions
from django.db import IntegrityError

from oscar.core.loading import get_model

Benefit = get_model('offer', 'Benefit')
Condition = get_model('offer', 'Condition')
Range = get_model('offer', 'Range')


def _class_path(klass):
    return '%s.%s' % (klass.__module__, klass.__name__)


def create_range(range_class):
    """
    Create a custom range instance from the passed range class

    This function creates the appropriate database record for this custom
    range, including setting the class path for the custom proxy class.
    """
    if not hasattr(range_class, 'name'):
        raise exceptions.ValidationError(
            "A custom range must have a name attribute")

    # Ensure range name is text (not gettext wrapper)
    if range_class.name.__class__.__name__ == '__proxy__':
        raise exceptions.ValidationError(
            "Custom ranges must have text names (not gettext proxies)")

    try:
        return Range.objects.create(
            name=range_class.name, proxy_class=_class_path(range_class))
    except IntegrityError:
        raise ValueError("The passed range already exists in the database.")


def create_condition(condition_class, **kwargs):
    """
    Create a custom condition instance
    """
    return Condition.objects.create(
        proxy_class=_class_path(condition_class), **kwargs)


def create_benefit(benefit_class, **kwargs):
    """
    Create a custom benefit instance
    """
    # The custom benefit_class must override __str__ and description to
    # avoid a recursion error
    if benefit_class.description is Benefit.description:
        raise RuntimeError("Your custom benefit must implement its own "
                           "'description' property")
    return Benefit.objects.create(
        proxy_class=_class_path(benefit_class), **kwargs)
