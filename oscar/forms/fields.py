from django.core.exceptions import ValidationError
from django.core.validators import URLValidator
from django.core.urlresolvers import resolve
from django.db import models
from django.http import Http404


class ExtendedURLField(models.CharField):
    u"""
    Custom field similar to URLField type field, however also accepting 
    and validating local relative URLs, ie. '/product/'
    """
    description = "Extended URL"

    def __init__(self, verbose_name=None, name=None, verify_exists=True, **kwargs):
        kwargs['max_length'] = kwargs.get('max_length', 200)
        models.CharField.__init__(self, verbose_name, name, **kwargs)
        self.is_local_url = False
        self.verify_exists = verify_exists
        
    def get_prep_value(self, value):
        u"""
        Make sure local URLs have preceding and trailing slashes 
        """
        if self.is_local_url == True:
            value = self.fix_local_url(value)
        return value

    def validate(self, value, model_instance):
        u"""
        Overrides global vaidate method to check whether URL is valid
        """
        v = URLValidator(verify_exists=self.verify_exists)
        try:
            v(value)
        except ValidationError, e:
            if (e.code == 'invalid_link'):
                raise ValidationError('This link appears to be broken')
            self.validate_local_url(value)

    def validate_local_url(self, value):
        u"""
        Validate local URL name
        """
        try:
            value = self.fix_local_url(value)
            
            if self.verify_exists:
                resolve(value)
            self.is_local_url = True
        except Http404:
            raise ValidationError('Specified page does not exist')

    def fix_local_url(self, value):
        u"""
        Puts preceding and trailing slashes to local URL name 
        """
        if value != '/': 
            value = '/' + value.strip('/') + '/' 
        return value
    