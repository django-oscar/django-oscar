from django import forms
from django.db.models import get_model
from django.utils.translation import ugettext_lazy as _


class ValidateReviewMixin(object):

    def clean_title(self):
        title = self.cleaned_data['title'].strip()
        if not title:
            raise forms.ValidationError(_("This field is required"))
        if len(title) > 100:
            excess = len(title) - 100
            raise forms.ValidationError(_("Please enter a short title (with %d fewer characters)") % excess)
        return title

    def clean_body(self):
        body = self.cleaned_data['body'].strip()
        if not body:
            raise forms.ValidationError(_("This field is required"))
        return body


class SignedInUserProductReviewForm(forms.ModelForm, ValidateReviewMixin):
    class Meta:
        model = get_model('reviews', 'productreview')
        fields = ('title', 'score', 'body')


class AnonymousUserProductReviewForm(forms.ModelForm, ValidateReviewMixin):
    name = forms.CharField(required=True)
    email = forms.EmailField(required=True)

    def clean_name(self):
        name = self.cleaned_data['name'].strip()
        if not name:
            raise forms.ValidationError(_("This field is required"))
        return name

    class Meta:
        model = get_model('reviews', 'productreview')
        fields = ('title', 'score', 'body', 'name', 'email',)


class VoteForm(forms.ModelForm):
    def clean(self):
        user = self.instance.user
        review = self.instance.review
        if review.user == user:
            raise forms.ValidationError(_("You cannot vote on your own reviews!"))
        return self.cleaned_data

    class Meta:
        model = get_model('reviews', 'vote')
        exclude = ('review', 'user',)
