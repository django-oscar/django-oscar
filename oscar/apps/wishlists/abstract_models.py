import hashlib
import random
from django.db import models
from django.utils.translation import ugettext_lazy as _
from oscar.core.compat import AUTH_USER_MODEL


class AbstractWishList(models.Model):
    """
    Represents a user's wish lists of products. A user can have multiple
    wish lists, move products between them, etc.
    """

    # Currently only authenticated users can have wishlists
    owner = models.ForeignKey(AUTH_USER_MODEL, related_name='wishlists',
                              verbose_name=_('Owner'))
    name = models.CharField(verbose_name=_('Name'), default=_('New Wish List'),
                            max_length=255)
    # This key is used for shared wish lists
    key = models.CharField(_('Key'), max_length=6, db_index=True, unique=True,
                           editable=False)

    PUBLIC, PRIVATE, SHARED = ('Public', 'Private', 'Shared')
    VISIBILITY_CHOICES = (
        (PRIVATE, _('Private - Only the owner can see the wish list')),
        (SHARED, _('Shared - Only the owner and people with access to the obfuscated link can see the wish list')),
        #(PUBLIC, _('Public - Everybody can see the wish list')),
    )
    visibility = models.CharField(
        _('Visibility'), max_length=20, default=PRIVATE, choices=VISIBILITY_CHOICES)

    # Convention: A user can have multiple wish lists. The last created wish
    # list for a user shall be her "default" wish list.
    # If an UI element only allows adding to wish list without
    # specifying which one , one shall use the default one.
    # That is a rare enough case to handle it by convention instead of a
    # BooleanField.
    created = models.DateTimeField(_('Creation date'),
                                   auto_now_add=True, editable=False)

    def __unicode__(self):
        return u"%s's Wish List '%s'" % (self.owner, self.name)

    def save(self, *args, **kwargs):
        if not self.pk or kwargs.get('force_insert', False):
            self.key = self.get_random_key()
        super(AbstractWishList, self).save(*args, **kwargs)

    def get_random_key(self, length=6):
        """
        Get a unique random generated key based on SHA-1 and owner
        """
        while True:
            key = hashlib.sha1(str(random.random())).hexdigest()[:length]
            if self.__class__._default_manager.filter(key=key).count() == 0:
                return key

    def is_allowed_to_see(self, user):
        if self.visibility in (self.PUBLIC, self.SHARED):
            return True
        else:
            return user == self.owner

    def is_allowed_to_edit(self, user):
        # currently only the owner can edit her wish list
        return user == self.owner

    class Meta:
        ordering = ('owner', 'created', )
        verbose_name = _('Wish List')
        abstract = True


class AbstractLine(models.Model):
    """
    One entry in a wish list. Similar to order lines or basket lines.
    """
    wishlist = models.ForeignKey('wishlists.WishList', related_name='lines',
                                 verbose_name=_('Wish List'))
    product = models.ForeignKey('catalogue.Product', verbose_name=_('Product'),
        related_name='wishlists_lines', on_delete=models.SET_NULL,
        blank=True, null=True)
    quantity = models.PositiveIntegerField(_('Quantity'), default=1)
    #: Store the title in case product gets deleted
    title = models.CharField(_("Title"), max_length=255)

    def __unicode__(self):
        return u'%sx %s on %s' % (self.quantity, self.title,
                                  self.wishlist.name)

    def get_title(self):
        if self.product:
            return self.product.get_title()
        else:
            return self.title

    class Meta:
        abstract = True
        verbose_name = _('Wish List Line')
        unique_together = (('wishlist', 'product'), )





