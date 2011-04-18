"""
Core product reviews
"""
from django.db import models
from django.contrib.auth.models import User
from django.utils.translation import gettext as _

from oscar.product.models import Item


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
    title = models.CharField(_("Title"), max_length=64)
    body = models.TextField(_("Body"), max_length=300, blank=True)
    score = models.CharField(_("Score"), max_length=1, choices=SCORE_CHOICES, blank=True)
    approved = models.BooleanField(default=False)
    
    class Meta:
        abstract = True
        ordering = ['approved']
        
    def get_absolute_url(self):
        return reverse('oscar-product-review-class', kwargs={'review_class_slug': self.slug})

    def __unicode__(self):
        return self.title

class AbstractVote(models.Model):
    u"""
    Records user ratings
    Each user can vote only once    
    """    
    user = models.ForeignKey('auth.User', related_name='vote', null=True, blank=True)
    review = models.ForeignKey('reviews.ProductReview', related_name='review')
    up = models.IntegerField(blank=True)
    down = models.IntegerField(blank=True)
    
    class Meta:
        abstract = True
        ordering = ['up']

    def __unicode__(self):
        return self.user.name
 