from django import template

register = template.Library()


@register.filter
def split(value, separator=' '):
    """
    Return a string split by the passed separator character (which defaults to
    space).

    Example usage:

    .. code-block:: html+django

        {% for tag in message.tags|split %}{{ tag }}{% endfor %}

    `Example usage in Oscar's templates`__

    __ https://github.com/tangentlabs/django-oscar/search?q=split+path%3A%2Foscar%2Ftemplates&type=Code
    """

    return value.split(separator)
