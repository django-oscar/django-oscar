from django.forms import fields

from oscar.core import validators


class ExtendedURLField(fields.URLField):
    """
    Custom field similar to URLField type field, however also accepting and
    validating local relative URLs, ie. '/product/'
    """

    def __init__(self, max_length=None, min_length=None, verify_exists=False,
            *args, **kwargs):
        # intentionally skip one step when calling super()
        super(fields.URLField, self).__init__(max_length, min_length, *args,
                                              **kwargs)
        validator = validators.ExtendedURLValidator(
            verify_exists=verify_exists)
        self.validators.append(validator)

    def to_python(self, value):
        # We need to avoid having 'http' inserted at the start of
        # every value
        if value and value.startswith('/'):
            return value
        return super(ExtendedURLField, self).to_python(value)
