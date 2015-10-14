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

    def __init__(self, max_length=None, min_length=None, verify_exists=None,
                 *args, **kwargs):
        # We don't pass on verify_exists as it has been deprecated in Django
        # 1.4
        super(fields.URLField, self).__init__(
            max_length, min_length, *args, **kwargs)
        # Even though it is deprecated, we still pass on 'verify_exists' as
        # Oscar's ExtendedURLValidator uses it to determine whether to test
        # local URLs.
        if verify_exists is not None:
            validator = validators.ExtendedURLValidator(
                verify_exists=verify_exists)
        else:
            validator = validators.ExtendedURLValidator()
        self.validators.append(validator)

    def to_python(self, value):
        # We need to avoid having 'http' inserted at the start of
        # every value so that local URLs are valid.
        if value and value.startswith('/'):
            return value
        return super(ExtendedURLField, self).to_python(value)
