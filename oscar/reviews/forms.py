from django.db import models
from django.forms import BaseForm, Form,  ModelForm, CharField, EmailField, Textarea, HiddenInput
from django.utils.translation import gettext as _

from oscar.reviews.models import ProductReview, Vote

class ProductReviewForm(ModelForm):    
    class Meta:
        model = ProductReview
        fields = ('title', 'score', 'body')

    def __init__(self, *args, **kwargs):
        super(ProductReviewForm, self).__init__(*args, **kwargs)

class UpVoteForm(Form):
    upvote = CharField(widget=HiddenInput,required=False, initial="up")

class DownVoteForm(Form):
    downvote = CharField(widget=HiddenInput,required=False, initial="down")
            
def make_review_form(user, values=None):
    form = ProductReviewForm()
    fields = form.fields    
    if not user.is_authenticated():
        fields['name'] = CharField(max_length=100)
        fields['email'] = EmailField()
        fields['url'] = CharField(max_length=100, required=False)        
    form_class = type('ProductReviewForm', (BaseForm,  ), { 'base_fields': fields }) 
    return form_class(values)

def make_voting_form(choice, values):
    if choice == 'up':
        form = UpVoteForm(values)
    elif choice == 'down':
        form = DownVoteForm(values)      
    return form