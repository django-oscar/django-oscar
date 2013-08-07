from django import forms
from django.db.models import get_model


Vote = get_model('reviews', 'vote')
ProductReview = get_model('reviews', 'productreview')


class ProductReviewForm(forms.ModelForm):
    name = forms.CharField(required=True)
    email = forms.EmailField(required=True)

    def __init__(self, user=None, *args, **kwargs):
        super(ProductReviewForm, self).__init__(*args, **kwargs)
        if user is not None and user.is_authenticated():
            del self.fields['name']
            del self.fields['email']

    class Meta:
        model = ProductReview
        fields = ('title', 'score', 'body', 'name', 'email')


class VoteForm(forms.ModelForm):

    def __init__(self, review, user, *args, **kwargs):
        super(VoteForm, self).__init__(*args, **kwargs)
        self.instance.review = review
        self.instance.user = user

    class Meta:
        model = Vote
        fields = ()
