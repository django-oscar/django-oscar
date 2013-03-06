from unidecode import unidecode
from django.template import defaultfilters


def slugify(value):
    return defaultfilters.slugify(unidecode(value))
