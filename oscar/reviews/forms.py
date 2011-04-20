from django.db import models
from django.forms import BaseForm, ModelForm, CharField, EmailField, Textarea
from django.utils.translation import gettext as _

from oscar.reviews.models import ProductReview

class ProductReviewForm(ModelForm):    
    class Meta:
        model = ProductReview
        fields = ('title', 'score', 'body')
        

def make_review_form(user):
    form = ProductReviewForm()
    fields = form.fields
    if not user.is_authenticated():
        fields['name'] = CharField(max_length=100)
        fields['email'] = EmailField()
        fields['url'] = CharField(max_length=100) 
    return type('ProductReviewForm', (BaseForm,  ), { 'base_fields': fields })
