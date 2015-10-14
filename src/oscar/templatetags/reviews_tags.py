from django import template

register = template.Library()


@register.filter
def as_stars(value):
    """
    Convert a float rating between 0 and 5 to a CSS class

    The CSS class name is the number of stars to be displayed.

    * Rounds to the nearest integer
    * Maps no rating to 0 stars
    * Fails quietly
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
    can_vote, __ = review.can_user_vote(user)
    return can_vote


@register.filter
def is_review_permitted(product, user):
    return product and product.is_review_permitted(user)
