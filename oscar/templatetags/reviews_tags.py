from django import template


register = template.Library()


@register.filter
def as_stars(value):
    """
    Convert a numeric value between 0 and 5 to a text version (for use in CSS).

    Usage:

    .. code-block:: html+django

        {{ 5|as_stars }}

    This will render "Five". More common usage:

    .. code-block:: html+django

        {{ product.rating|as_stars }}

    `Example usage in Oscar's templates`__

    __ https://github.com/tangentlabs/django-oscar/search?q=as_stars+path%3A%2Foscar%2Ftemplates&type=Code
    """
    num_stars_to_class = {
        0: '',
        1: 'One',
        2: 'Two',
        3: 'Three',
        4: 'Four',
        5: 'Five',
    }
    num_stars = int(round(value or 0.0))
    return num_stars_to_class.get(num_stars, '')


@register.filter
def may_vote(review, user):
    """
    Returns a boolean indicating if a given user can vote on a review.

    Usage:

    .. code-block:: html+django

        {% if review|may_vote:user %}
            ...
        {% endif %}

    `Example usage in Oscar's templates`__

    __ https://github.com/tangentlabs/django-oscar/search?q=may_vote+path%3A%2Foscar%2Ftemplates&type=Code
    """
    can_vote, __ = review.can_user_vote(user)
    return can_vote


@register.filter
def is_review_permitted(product, user):
    """
    Returns a boolean indicating if a given user may review a given product.

    Usage:

    .. code-block:: html+django

        {% if product|is_review_permitted:user %}
            ...
        {% endif %}

    `Example usage in Oscar's templates`__

    __ https://github.com/tangentlabs/django-oscar/search?q=is_review_permitted+path%3A%2Foscar%2Ftemplates&type=Code
    """
    return product and product.is_review_permitted(user)
