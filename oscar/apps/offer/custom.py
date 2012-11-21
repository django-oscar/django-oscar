from django.core import exceptions

from oscar.apps.offer.models import Range


def create_range(range_class):
    """
    Create a custom range instance
    """
    if not hasattr(range_class, 'name'):
        raise exceptions.ValidationError(
            "A custom range must have a name attribute")
    klass_path = '%s.%s' % (range_class.__module__,
                            range_class.__name__)
    return Range.objects.create(
        name=range_class.name,
        proxy_class=klass_path)
