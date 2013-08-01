from django import forms
from django.db.models import get_model
from django.utils.translation import ugettext_lazy as _


Vote = get_model('reviews', 'vote')
ProductReview = get_model('reviews', 'productreview')


class ProductReviewForm(forms.ModelForm):
    name = forms.CharField(required=True)
    email = forms.EmailField(required=True)

    def __init__(self, user=None, *args, **kwargs):
        super(ProductReviewForm, self).__init__(*args, **kwargs)
        if user is not None and user.is_authenticated():
            self.user = user
            del self.fields['name']
            del self.fields['email']

    class Meta:
        model = ProductReview
        fields = ('title', 'score', 'body', 'name', 'email')


class VoteForm(forms.ModelForm):
    def clean(self):
        vote = self.instance
        if vote.review.user == vote.user:
            raise forms.ValidationError(
                _("You cannot vote on your own reviews!"))
        return self.cleaned_data

    class Meta:
        model = Vote
        fields = ('delta', )
