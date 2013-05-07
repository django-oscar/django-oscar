from django.core import exceptions

from oscar.apps.offer.models import Range, Condition, Benefit


def _class_path(klass):
    return '%s.%s' % (klass.__module__, klass.__name__)


def create_range(range_class):
    """
    Create a custom range instance
    """
    if not hasattr(range_class, 'name'):
        raise exceptions.ValidationError(
            "A custom range must have a name attribute")
    return Range.objects.create(
        name=range_class.name,
        proxy_class=_class_path(range_class))


def create_condition(condition_class):
    """
    Create a custom condition instance
    """
    return Condition.objects.create(
        proxy_class=_class_path(condition_class))


def create_benefit(benefit_class):
    """
    Create a custom benefit instance
    """
    # The custom benefit_class must override __unicode__ and description to
    # avoid a recursion error
    if benefit_class.description is Benefit.description:
        raise RuntimeError("Your custom benefit must implement its own "
                           "'description' property")
    return Benefit.objects.create(
        proxy_class=_class_path(benefit_class))
