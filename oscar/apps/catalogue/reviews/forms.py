from django import forms
from django.db.models import get_model

class SignedInUserProductReviewForm(forms.ModelForm):
    class Meta:
        model = get_model('reviews', 'productreview')
        fields = ('title', 'score', 'body')
        
        
class AnonymousUserProductReviewForm(forms.ModelForm):
    name = forms.CharField(required=True)
    email = forms.EmailField(required=True)
    
    class Meta:
        model = get_model('reviews', 'productreview')
        fields = ('title', 'score', 'body', 'name', 'email', 'homepage')


class VoteForm(forms.ModelForm):
    def clean(self):
        user = self.instance.user
        review = self.instance.review  
        if review.user == user:
            raise forms.ValidationError("You cannot vote on your own reviews!")
        return self.cleaned_data
    
    class Meta:
        model = get_model('reviews', 'vote')
        exclude = ('review', 'user',)