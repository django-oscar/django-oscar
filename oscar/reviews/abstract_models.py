"""
Core product reviews
"""
from django.db import models
from django.utils.translation import gettext as _
from django.core.urlresolvers import reverse

class AbstractProductReview(models.Model):
    u"""
    Superclass ProductReview

    The required fields are title and score
    """
    SCORE_CHOICES = (
        ('1', 1),
        ('2', 2),
        ('3', 3),
        ('4', 4),
        ('5', 5)
    )
    product = models.ForeignKey('product.Item', related_name='product')
    user = models.ForeignKey('auth.User', related_name='review', null=True)
    # anonymous users
    name = models.CharField(_("Name"), max_length=100, null=True, blank=True)
    email = models.EmailField(_("Email"), null=True, blank=True)
    url = models.URLField(_("URL"), null=True, blank=True)
    # real review stuffs
    title = models.CharField(_("Title"), max_length=100)
    body = models.TextField(_("Comment"), max_length=300, blank=True)
    score = models.CharField(_("Score"), max_length=1, choices=SCORE_CHOICES)
    approved = models.BooleanField(default=False)
    date_created = models.DateTimeField(auto_now_add=True)

    class Meta:
        abstract = True
        ordering = ['approved']

    @models.permalink
    def get_absolute_url(self):
        return reverse('oscar-product-review', 
                       kwargs={'review_id': self.id,
                               'item_class_slug': str(self.product.item_class),
                               'item_slug': self.product.slug, 
                                'item_id': str(self.product.id)})

    def get_vote_url(self):                
        return reverse('oscar-vote-review', 
                       kwargs={'review_id': self.id,
                               'item_class_slug': str(self.product.item_class),
                               'item_slug': self.product.slug, 
                                'item_id': str(self.product.id)})

    def __unicode__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.title:
            from django.core.exceptions import ValidationError
            raise ValidationError("Review must have a title")
        super(AbstractProductReview, self).save(*args, **kwargs)



class AbstractVote(models.Model):
    u"""
    Records user ratings
    Each user can vote only once    
    """    
    user = models.ForeignKey('auth.User', related_name='vote', null=True, blank=True)
    review = models.ForeignKey('reviews.ProductReview', related_name='review')
    up = models.IntegerField(_("VoteUp"))
    down = models.IntegerField(_("VoteDown"))
    date_created = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        abstract = True
        ordering = ['up']
        
    def __unicode__(self):
        return self.review.title 
    
    def save(self, *args, **kwargs):
        if (not self.up) or (not self.down):
            from django.core.exceptions import ValidationError
            raise ValidationError("Votes should be either up or down")
        super(AbstractVote, self).save(*args, **kwargs)