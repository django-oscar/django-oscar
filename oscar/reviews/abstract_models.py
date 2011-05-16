"""
Core product reviews
"""
from django.db import models
from django.utils.translation import gettext as _
from django.core.urlresolvers import reverse

from oscar.reviews.managers import ApprovedReviewsManager, RecentReviewsManager, TopScoredReviewsManager

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
    user = models.ForeignKey('auth.User', related_name='review', null=True, blank=True)
    # anonymous users
    name = models.CharField(_("Name"), max_length=100, null=True, blank=True)
    email = models.EmailField(_("Email"), null=True, blank=True, unique=True)
    url = models.URLField(_("URL"), null=True, blank=True)
    # real review stuffs
    title = models.CharField(_("Title"), max_length=100)
    body = models.TextField(_("Comment"), max_length=300, blank=True)
    score = models.CharField(_("Score"), max_length=1, choices=SCORE_CHOICES)
    approved = models.BooleanField(default=False)
    date_created = models.DateTimeField(auto_now_add=True)
    #up_votes = models.IntegerField(_("UpVotes"), null=True, blank=True, editable=False)
    #down_votes = models.IntegerField(_("DownVotes"), null=True, blank=True, editable=False)
        
    # mangers
    objects = models.Manager()
    approved_only = ApprovedReviewsManager()
    recent = RecentReviewsManager()
    top_scored = TopScoredReviewsManager()

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
        if not self.user: # anonymous review
            if not (self.name and self.email):
                from django.core.exceptions import ValidationError
                raise ValidationError("Review must have a name and an email")
        super(AbstractProductReview, self).save(*args, **kwargs)
     
    # helpers
    def count_votes(self, votes):
        u"""
        Get the number of votes for this review
        """
        return votes.objects.filter(review=self.id).count()
                     

class AbstractVote(models.Model):
    u"""
    Records user ratings
    Each user can vote only once    
    """    
    user = models.ForeignKey('auth.User', related_name='vote')
    review = models.ForeignKey('reviews.ProductReview', related_name='review')
    up = models.IntegerField(_("VoteUp"), null=True, blank=True)
    down = models.IntegerField(_("VoteDown"), null=True, blank=True)
    date_created = models.DateTimeField(auto_now_add=True)
    
    objects = models.Manager()
        
    class Meta:
        abstract = True
        ordering = ['up']
                        
    def __unicode__(self):
        return self.review.title 
    
    def save(self, *args, **kwargs):
        if not (self.up or self.down):
            from django.core.exceptions import ValidationError
            raise ValidationError("Votes should be either up or down")
        super(AbstractVote, self).save(*args, **kwargs)

 