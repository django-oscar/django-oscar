from django.forms import TextInput, fields

from oscar.core import validators


class ExtendedURLField(fields.URLField):
    """
    Custom field similar to URLField type field, however also accepting and
    validating local relative URLs, ie. '/product/'
    """

    default_validators = []
    # Django 1.6 renders URLInput as <input type=url>, which causes some
    # browsers to require the input to be a valid absolute URL. As relative
    # URLS are allowed for ExtendedURLField, we must set it to TextInput
    widget = TextInput

    def __init__(self, *args, **kwargs):
        super(fields.URLField, self).__init__(*args, **kwargs)
        self.validators.append(validators.ExtendedURLValidator())

    def to_python(self, value):
        # We need to avoid having 'http' inserted at the start of
        # every value so that local URLs are valid.
        if value and value.startswith("/"):
            return value
        return super().to_python(value)
