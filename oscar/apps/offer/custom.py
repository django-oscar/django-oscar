import six

from django.core import exceptions

from oscar.apps.offer.models import Range, Condition, Benefit


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

    # Ensure range name is text (not ugettext wrapper)
    if range_class.name.__class__.__name__ == '__proxy__':
        raise exceptions.ValidationError(
            "Custom ranges must have text names (not ugettext proxies)")

    # In Django versions further than 1.6 it will be update_or_create
    # https://docs.djangoproject.com/en/dev/ref/models/querysets/#update-or-create # noqa
    values = {
        'name': range_class.name,
        'proxy_class': _class_path(range_class),
    }
    try:
        obj = Range.objects.get(**values)
    except Range.DoesNotExist:
        obj = Range(**values)
    else:
        for key, value in six.iteritems(values):
            setattr(obj, key, value)
    obj.save()

    return obj


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
