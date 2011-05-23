"""
Core product reviews
"""
from django.db import models
from django.utils.translation import gettext as _
from django.core.urlresolvers import reverse
from django.core.exceptions import ValidationError

from oscar.apps.reviews.managers import ApprovedReviewsManager,\
 RecentReviewsManager, TopScoredReviewsManager, TopVotedReviewsManager


class AbstractProductReview(models.Model):
    u"""
    Superclass ProductReview. Some key aspects have been implemented from the original spec.
    * Each product can have reviews attached to it. Each review has a title, a body and a score from 1-5.
    * Signed in users can always submit reviews, anonymous users can only submit reviews if a setting
      OSCAR_ALLOW_ANON_REVIEWS is set to true - it should default to false.
    * If anon users can submit reviews, then we require their name, email address and an (optional) URL.
    * By default, reviews must be approved before they are live.
      However, if a setting OSCAR_MODERATE_REVIEWS is set to false, then they don't need moderation.
    * Each review should have a permalink, ie it has its own page.
    * Each reviews can be voted up or down by other users
    * Only signed in users can vote
    * A user can only vote once on each product once
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
    # vote statistics
    total_votes = models.IntegerField(_("Total Votes"), default=0, blank=True)  # upvotes + down votes
    delta_votes = models.IntegerField(_("Delta Votes"), default=0, blank=True)  # upvotes - down votes
    # mangers
    objects = models.Manager()
    approved_only = ApprovedReviewsManager()
    recent = RecentReviewsManager()
    top_scored = TopScoredReviewsManager()
    top_voted = TopVotedReviewsManager()

    class Meta:
        abstract = True
        ordering = ['-delta_votes']

    def get_absolute_url(self):
        args = {'review_id': self.id,
                'item_class_slug': self.product.get_item_class().slug,
                'item_slug': self.product.slug,
                'item_id': self.product.id}
        return reverse('oscar-product-review',  kwargs=args)

    def get_vote_url(self):
        return reverse('oscar-vote-review',
                       kwargs={'review_id': self.id,
                               'item_class_slug': str(self.product.item_class),
                               'item_slug': self.product.slug,
                                'item_id': str(self.product.id)})

    def __unicode__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not (self.title and self.score):
            raise ValidationError("Review must have a title")
        if not self.user:  # anonymous review
            if not (self.name and self.email):
                raise ValidationError("Anonymous review must have a name and an email")
        super(AbstractProductReview, self).save(*args, **kwargs)

    def get_upvotes(self):
        u"""returns the total yes votes"""
        return int((self.total_votes + self.delta_votes) / 2)

    def update_votes(self, choice):
        u""" updates total and delta votes"""
        self.total_votes += 1
        self.delta_votes += choice
        self.save()


class AbstractVote(models.Model):
    u"""
    Records user ratings as yes/no vote.
    * Only signed-in users can vote.
    * Each user can vote only once.
    """
    VOTE_CHOICES = ((1, 1), (-1, -1), (0, 0))
    user = models.ForeignKey('auth.User', related_name='vote')
    review = models.ForeignKey('reviews.ProductReview', related_name='review')
    choice = models.SmallIntegerField(choices=VOTE_CHOICES)
    date_created = models.DateTimeField(auto_now_add=True)

    objects = models.Manager()

    class Meta:
        abstract = True
        ordering = ['-date_created']
        unique_together = (('user', 'review'),)

    def __unicode__(self):
        return self.review.title

    def save(self, *args, **kwargs):
        u"""
        Validates model and raises error if validation fails
        """
        if not self.user.is_authenticated():
                raise ValidationError("Only logged-in users can vote!")
        if self.choice == None:
            raise ValidationError("Votes must have a choice (Yes/No)")
        if self.choice == 0:  # empty vote
            return
        else:
            self.review.update_votes(self.choice)
        super(AbstractVote, self).save(*args, **kwargs)
