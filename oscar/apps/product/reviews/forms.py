from django.forms import ModelForm, CharField, EmailField
from django.db.models import get_model

class SignedInUserProductReviewForm(ModelForm):
    class Meta:
        model = get_model('reviews', 'productreview')
        fields = ('title', 'score', 'body')
        
        
class AnonymousUserProductReviewForm(ModelForm):
    name = CharField(required=True)
    email = EmailField(required=True)
    
    class Meta:
        model = get_model('reviews', 'productreview')
        fields = ('title', 'score', 'body', 'name', 'email', 'homepage')


class VoteForm(ModelForm):
    class Meta:
        model = get_model('reviews', 'vote')
        exclude = ('review', 'user',)