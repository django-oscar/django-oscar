from django.db import models
from django.urls import reverse
from django.utils.crypto import get_random_string
from django.utils.translation import gettext_lazy as _
from django.utils.translation import pgettext_lazy

from oscar.core.compat import AUTH_USER_MODEL


class AbstractWishList(models.Model):
    """
    Represents a user's wish lists of products.

    A user can have multiple wish lists, move products between them, etc.
    """

    # Only authenticated users can have wishlists
    owner = models.ForeignKey(
        AUTH_USER_MODEL,
        related_name='wishlists',
        on_delete=models.CASCADE,
        verbose_name=_('Owner'))
    name = models.CharField(verbose_name=_('Name'), default=_('Default'),
                            max_length=255)

    #: This key acts as primary key and is used instead of an int to make it
    #: harder to guess
    key = models.CharField(_('Key'), max_length=6, db_index=True, unique=True,
                           editable=False)

    # Oscar core does not support public or shared wishlists at the moment, but
    # all the right hooks should be there
    PUBLIC, PRIVATE, SHARED = ('Public', 'Private', 'Shared')
    VISIBILITY_CHOICES = (
        (PRIVATE, _('Private - Only the owner can see the wish list')),
        (SHARED, _('Shared - Only the owner and people with access to the'
                   ' obfuscated link can see the wish list')),
        (PUBLIC, _('Public - Everybody can see the wish list')),
    )
    visibility = models.CharField(_('Visibility'), max_length=20,
                                  default=PRIVATE, choices=VISIBILITY_CHOICES)

    # Convention: A user can have multiple wish lists. The last created wish
    # list for a user shall be their "default" wish list.
    # If an UI element only allows adding to wish list without
    # specifying which one , one shall use the default one.
    # That is a rare enough case to handle it by convention instead of a
    # BooleanField.
    date_created = models.DateTimeField(
        _('Date created'), auto_now_add=True, editable=False, db_index=True)

    def __str__(self):
        return "%s's Wish List '%s'" % (self.owner, self.name)

    def save(self, *args, **kwargs):
        if not self.pk or kwargs.get('force_insert', False):
            self.key = self.__class__.random_key()
        super().save(*args, **kwargs)

    @classmethod
    def random_key(cls, length=6):
        """
        Get a unique random generated key
        """
        while True:
            key = get_random_string(length=length,
                                    allowed_chars='abcdefghijklmnopqrstuvwxyz0123456789')
            if not cls._default_manager.filter(key=key).exists():
                return key

    def is_allowed_to_see(self, user):
        if user == self.owner:
            return True
        elif self.visibility == self.PUBLIC:
            return True
        elif self.visibility == self.SHARED and user.is_authenticated:
            return self.shared_emails.filter(email=user.email).exists()
        return False

    def is_allowed_to_edit(self, user):
        # currently only the owner can edit their wish list
        return user == self.owner

    class Meta:
        abstract = True
        app_label = 'wishlists'
        ordering = ('owner', 'date_created', )
        verbose_name = _('Wish List')

    def get_absolute_url(self):
        return reverse('customer:wishlists-detail', kwargs={
            'key': self.key})

    def add(self, product):
        """
        Add a product to this wishlist
        """
        lines = self.lines.filter(product=product)
        if len(lines) == 0:
            self.lines.create(
                product=product, title=product.get_title())
        else:
            line = lines[0]
            line.quantity += 1
            line.save()

    def get_shared_url(self):
        return reverse("wishlists:detail", kwargs={
            'key': self.key})

    @property
    def is_shareable(self):
        return self.visibility in [self.PUBLIC, self.SHARED]


class AbstractLine(models.Model):
    """
    One entry in a wish list. Similar to order lines or basket lines.
    """
    wishlist = models.ForeignKey(
        'wishlists.WishList',
        on_delete=models.CASCADE,
        related_name='lines',
        verbose_name=_('Wish List'))
    product = models.ForeignKey(
        'catalogue.Product', verbose_name=_('Product'),
        related_name='wishlists_lines', on_delete=models.SET_NULL,
        blank=True, null=True)
    quantity = models.PositiveIntegerField(_('Quantity'), default=1)
    #: Store the title in case product gets deleted
    title = models.CharField(
        pgettext_lazy("Product title", "Title"), max_length=255)

    def __str__(self):
        return '%sx %s on %s' % (self.quantity, self.title, self.wishlist.name)

    def get_title(self):
        if self.product:
            return self.product.get_title()
        else:
            return self.title

    class Meta:
        abstract = True
        app_label = 'wishlists'
        # Enforce sorting by order of creation.
        ordering = ['pk']
        unique_together = (('wishlist', 'product'), )
        verbose_name = _('Wish list line')


class AbstractWishListSharedEmail(models.Model):
    """
    An email which is allowed to view and possibly edit the wishlist, if shared.
    The user will have to login/create an account with this email in order to view it.
    """
    wishlist = models.ForeignKey(
        'wishlists.WishList',
        on_delete=models.CASCADE,
        related_name='shared_emails',
        verbose_name=_('Wish List'))
    email = models.EmailField(verbose_name=_('Email'))

    def __str__(self):
        return "%s - %s" % (self.wishlist.name, self.email)

    class Meta:
        abstract = True
        app_label = 'wishlists'
        verbose_name = _('Wish list shared email')
