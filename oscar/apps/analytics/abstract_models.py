from decimal import Decimal

from django.db import models
from django.utils.translation import ugettext as _


class AbstractProductRecord(models.Model):
    """
    A record of a how popular a product is.

    This used be auto-merchandising to display the most popular
    products.
    """

    product = models.OneToOneField(
        'catalogue.Product', verbose_name=_("Product"),
        related_name='stats')

    # Data used for generating a score
    num_views = models.PositiveIntegerField(_('Views'), default=0)
    num_basket_additions = models.PositiveIntegerField(
        _('Basket Additions'), default=0)
    num_purchases = models.PositiveIntegerField(
        _('Purchaes'), default=0, db_index=True)

    # Product score - used within search
    score = models.FloatField(_('Score'), default=0.00)

    class Meta:
        abstract = True
        ordering = ['-num_purchases']
        verbose_name = _('Product record')
        verbose_name_plural = _('Product records')

    def __unicode__(self):
        return _("Record for '%s'") % self.product


class AbstractUserRecord(models.Model):
    """
    A record of a user's activity.
    """

    user = models.OneToOneField('auth.User', verbose_name=_("User"))

    # Browsing stats
    num_product_views = models.PositiveIntegerField(
        _('Product Views'), default=0)
    num_basket_additions = models.PositiveIntegerField(
        _('Basket Additions'), default=0)

    # Order stats
    num_orders = models.PositiveIntegerField(
        _('Orders'), default=0, db_index=True)
    num_order_lines = models.PositiveIntegerField(
        _('Order Lines'), default=0, db_index=True)
    num_order_items = models.PositiveIntegerField(
        _('Order Items'), default=0, db_index=True)
    total_spent = models.DecimalField(_('Total Spent'), decimal_places=2,
                                      max_digits=12, default=Decimal('0.00'))
    date_last_order = models.DateTimeField(
        _('Last Order Date'), blank=True, null=True)

    class Meta:
        abstract = True
        verbose_name = _('User Record')
        verbose_name_plural = _('User Records')


class AbstractUserProductView(models.Model):

    user = models.ForeignKey('auth.User', verbose_name=_("User"))
    product = models.ForeignKey('catalogue.Product', verbose_name=_("Product"))
    date_created = models.DateTimeField(_("Date Created"), auto_now_add=True)

    class Meta:
        abstract = True
        verbose_name = _('Basket')
        verbose_name_plural = _('Baskets')

    def __unicode__(self):
        return _("%(user)s viewed '%(product)s'") % {
            'user': self.user, 'product': self.product}


class AbstractUserSearch(models.Model):

    user = models.ForeignKey('auth.User', verbose_name=_("User"))
    query = models.CharField(_("Search term"), max_length=255, db_index=True)
    date_created = models.DateTimeField(_("Date Created"), auto_now_add=True)

    class Meta:
        abstract = True
        verbose_name_plural = _("User search queries")

    def __unicode__(self):
        return _("%(user)s searched for '%(query)s'") % {
            'user': self.user,
            'query': self.query}
