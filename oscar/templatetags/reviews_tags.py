from django import template
from django.conf import settings
from django.db.models.fields.files import ImageFieldFile

register = template.Library()

@register.filter
def as_stars(value):
    """
    Returns the numbers of stars to be displayed, mapped to
    CSS classes in the frontend.
    * Rounds to the nearest integer
    * Maps no rating to 0 stars
    * Fails quietly
    """
    num_stars_to_class = {0: '', 1: 'One', 2: 'Two', 3: 'Three',
                          4: 'Four', 5: 'Five'}
    num_stars = int(round(value or 0.0))
    return num_stars_to_class.get(num_stars, '')

