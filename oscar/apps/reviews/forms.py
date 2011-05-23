from django.forms import BaseForm, ModelForm, CharField, EmailField

from oscar.apps.reviews.models import ProductReview


class ProductReviewForm(ModelForm):
    class Meta:
        model = ProductReview
        fields = ('title', 'score', 'body')

    def __init__(self, *args, **kwargs):
        super(ProductReviewForm, self).__init__(*args, **kwargs)


def make_review_form(user, values=None):
    form = ProductReviewForm()
    fields = form.fields
    if not user.is_authenticated():
        fields['name'] = CharField(max_length=100)
        fields['email'] = EmailField()
        fields['url'] = CharField(max_length=100, required=False)
    form_class = type('ProductReviewForm', (BaseForm,), {'base_fields': fields})
    return form_class(values)
