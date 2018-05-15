from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Count, Sum
from django.urls import reverse
from django.utils.encoding import python_2_unicode_compatible
from django.utils.translation import ugettext_lazy as _
from django.utils.translation import pgettext_lazy

from oscar.apps.catalogue.reviews.utils import get_default_review_status
from oscar.core import validators
from oscar.core.compat import AUTH_USER_MODEL
from oscar.core.loading import get_class


ProductReviewQuerySet = get_class('catalogue.reviews.managers', 'ProductReviewQuerySet')


@python_2_unicode_compatible
class AbstractProductReview(models.Model):
    """
    A review of a product

    Reviews can belong to a user or be anonymous.
    """

    product = models.ForeignKey(
        'catalogue.Product', related_name='reviews', null=True,
        on_delete=models.CASCADE)

    # Scores are between 0 and 5
    SCORE_CHOICES = tuple([(x, x) for x in range(0, 6)])
    score = models.SmallIntegerField(_("Score"), choices=SCORE_CHOICES)

    title = models.CharField(
        verbose_name=pgettext_lazy(u"Product review title", u"Title"),
        max_length=255, validators=[validators.non_whitespace])

    body = models.TextField(_("Body"))

    # User information.
    user = models.ForeignKey(
        AUTH_USER_MODEL,
        blank=True,
        null=True,
        on_delete=models.CASCADE,
        related_name='reviews')

    # Fields to be completed if user is anonymous
    name = models.CharField(
        pgettext_lazy(u"Anonymous reviewer name", u"Name"),
        max_length=255, blank=True)
    email = models.EmailField(_("Email"), blank=True)
    homepage = models.URLField(_("URL"), blank=True)

    FOR_MODERATION, APPROVED, REJECTED = 0, 1, 2
    STATUS_CHOICES = (
        (FOR_MODERATION, _("Requires moderation")),
        (APPROVED, _("Approved")),
        (REJECTED, _("Rejected")),
    )

    status = models.SmallIntegerField(
        _("Status"), choices=STATUS_CHOICES, default=get_default_review_status)

    # Denormalised vote totals
    total_votes = models.IntegerField(
        _("Total Votes"), default=0)  # upvotes + down votes
    delta_votes = models.IntegerField(
        _("Delta Votes"), default=0, db_index=True)  # upvotes - down votes

    date_created = models.DateTimeField(auto_now_add=True)

    # Managers
    objects = ProductReviewQuerySet.as_manager()

    class Meta:
        abstract = True
        app_label = 'reviews'
        ordering = ['-delta_votes', 'id']
        unique_together = (('product', 'user'),)
        verbose_name = _('Product review')
        verbose_name_plural = _('Product reviews')

    def get_absolute_url(self):
        kwargs = {
            'product_slug': self.product.slug,
            'product_pk': self.product.id,
            'pk': self.id
        }
        return reverse('catalogue:reviews-detail', kwargs=kwargs)

    def __str__(self):
        return self.title

    def clean(self):
        self.title = self.title.strip()
        self.body = self.body.strip()
        if not self.user and not (self.name and self.email):
            raise ValidationError(
                _("Anonymous reviews must include a name and an email"))

    def vote_up(self, user):
        self.votes.create(user=user, delta=AbstractVote.UP)

    def vote_down(self, user):
        self.votes.create(user=user, delta=AbstractVote.DOWN)

    def save(self, *args, **kwargs):
        super(AbstractProductReview, self).save(*args, **kwargs)
        self.product.update_rating()

    def delete(self, *args, **kwargs):
        super(AbstractProductReview, self).delete(*args, **kwargs)
        if self.product is not None:
            self.product.update_rating()

    # Properties

    @property
    def is_anonymous(self):
        return self.user is None

    @property
    def pending_moderation(self):
        return self.status == self.FOR_MODERATION

    @property
    def is_approved(self):
        return self.status == self.APPROVED

    @property
    def is_rejected(self):
        return self.status == self.REJECTED

    @property
    def has_votes(self):
        return self.total_votes > 0

    @property
    def num_up_votes(self):
        """Returns the total up votes"""
        return int((self.total_votes + self.delta_votes) / 2)

    @property
    def num_down_votes(self):
        """Returns the total down votes"""
        return int((self.total_votes - self.delta_votes) / 2)

    @property
    def reviewer_name(self):
        if self.user:
            name = self.user.get_full_name()
            return name if name else _('anonymous')
        else:
            return self.name

    # Helpers

    def update_totals(self):
        """
        Update total and delta votes
        """
        result = self.votes.aggregate(
            score=Sum('delta'), total_votes=Count('id'))
        self.total_votes = result['total_votes'] or 0
        self.delta_votes = result['score'] or 0
        self.save()

    def can_user_vote(self, user):
        """
        Test whether the passed user is allowed to vote on this
        review
        """
        if not user.is_authenticated:
            return False, _(u"Only signed in users can vote")
        vote = self.votes.model(review=self, user=user, delta=1)
        try:
            vote.full_clean()
        except ValidationError as e:
            return False, u"%s" % e
        return True, ""


@python_2_unicode_compatible
class AbstractVote(models.Model):
    """
    Records user ratings as yes/no vote.

    * Only signed-in users can vote.
    * Each user can vote only once.
    """
    review = models.ForeignKey(
        'reviews.ProductReview',
        on_delete=models.CASCADE,
        related_name='votes')
    user = models.ForeignKey(
        AUTH_USER_MODEL,
        related_name='review_votes',
        on_delete=models.CASCADE)
    UP, DOWN = 1, -1
    VOTE_CHOICES = (
        (UP, _("Up")),
        (DOWN, _("Down"))
    )
    delta = models.SmallIntegerField(_('Delta'), choices=VOTE_CHOICES)
    date_created = models.DateTimeField(auto_now_add=True)

    class Meta:
        abstract = True
        app_label = 'reviews'
        ordering = ['-date_created']
        unique_together = (('user', 'review'),)
        verbose_name = _('Vote')
        verbose_name_plural = _('Votes')

    def __str__(self):
        return u"%s vote for %s" % (self.delta, self.review)

    def clean(self):
        if not self.review.is_anonymous and self.review.user == self.user:
            raise ValidationError(_(
                "You cannot vote on your own reviews"))
        if not self.user.id:
            raise ValidationError(_(
                "Only signed-in users can vote on reviews"))
        previous_votes = self.review.votes.filter(user=self.user)
        if len(previous_votes) > 0:
            raise ValidationError(_(
                "You can only vote once on a review"))

    def save(self, *args, **kwargs):
        super(AbstractVote, self).save(*args, **kwargs)
        self.review.update_totals()
