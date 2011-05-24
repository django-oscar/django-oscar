from django.forms import BaseForm, ModelForm, CharField, EmailField

from oscar.core.loading import import_module
import_module('product.reviews.models', ['ProductReview'], locals())


class SignedInUserProductReviewForm(ModelForm):
    
    class Meta:
        model = ProductReview
        fields = ('title', 'score', 'body')
        
        
class AnonymousUserProductReviewForm(ModelForm):
    
    name = CharField(required=True)
    email = EmailField(required=True)
    
    class Meta:
        model = ProductReview
        fields = ('title', 'score', 'body', 'name', 'email', 'homepage')


