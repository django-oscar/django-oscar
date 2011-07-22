from django.forms import fields

from oscar.core import validators

class ExtendedURLField(fields.URLField):
    """
    Custom field similar to URLField type field, however also accepting 
    and validating local relative URLs, ie. '/product/'
    """

    def __init__(self, max_length=None, min_length=None, verify_exists=False,
            validator_user_agent=validators.URL_VALIDATOR_USER_AGENT, *args, **kwargs):
        # intentionally skip one step when calling super()
        super(fields.URLField, self).__init__(max_length, min_length, *args,
                                       **kwargs)
        validator = validators.ExtendedURLValidator(verify_exists=verify_exists,
                                                    validator_user_agent=validator_user_agent)
        self.validators.append(validator)
