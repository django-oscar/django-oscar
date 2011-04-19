from django.db import models
from django.forms import ModelForm

from oscar.reviews.models import ProductReview

class ProductReviewForm(ModelForm):    
    class Meta:
        model = ProductReview
        fields = ('title', 'score', 'body')
