from decimal import Decimal

from django.db import models
from django.utils.translation import gettext_lazy as _

from oscar.core.compat import AUTH_USER_MODEL
from oscar.core.utils import get_default_currency
from oscar.models.fields import AutoSlugField
from oscar.templatetags.currency_filters import currency

from . import bankcards


class AbstractTransaction(models.Model):
    """
    A transaction for a particular payment source.

    These are similar to the payment events within the order app but model a
    slightly different aspect of payment.  Crucially, payment sources and
    transactions have nothing to do with the lines of the order while payment
    events do.

    For example:
    * A ``pre-auth`` with a bankcard gateway
    * A ``settle`` with a credit provider (see :py:mod:`django-oscar-accounts`)
    """

    source = models.ForeignKey(
        "payment.Source",
        on_delete=models.CASCADE,
        related_name="transactions",
        verbose_name=_("Source"),
    )

    # We define some sample types but don't constrain txn_type to be one of
    # these as there will be domain-specific ones that we can't anticipate
    # here.
    AUTHORISE, DEBIT, REFUND = "Authorise", "Debit", "Refund"
    txn_type = models.CharField(_("Type"), max_length=128, blank=True)

    amount = models.DecimalField(_("Amount"), decimal_places=2, max_digits=12)
    reference = models.CharField(_("Reference"), max_length=128, blank=True)
    status = models.CharField(_("Status"), max_length=128, blank=True)
    date_created = models.DateTimeField(
        _("Date Created"), auto_now_add=True, db_index=True
    )

    def __str__(self):
        return _("%(type)s of %(amount).2f") % {
            "type": self.txn_type,
            "amount": self.amount,
        }

    class Meta:
        abstract = True
        app_label = "payment"
        ordering = ["-date_created"]
        verbose_name = _("Transaction")
        verbose_name_plural = _("Transactions")


class AbstractSource(models.Model):
    """
    A source of payment for an order.

    This is normally a credit card which has been pre-authorised for the order
    amount, but some applications will allow orders to be paid for using
    multiple sources such as cheque, credit accounts, gift cards. Each payment
    source will have its own entry.

    This source object tracks how much money has been authorised, debited and
    refunded, which is useful when payment takes place in multiple stages.
    """

    order = models.ForeignKey(
        "order.Order",
        on_delete=models.CASCADE,
        related_name="sources",
        verbose_name=_("Order"),
    )
    source_type = models.ForeignKey(
        "payment.SourceType",
        on_delete=models.CASCADE,
        related_name="sources",
        verbose_name=_("Source Type"),
    )
    currency = models.CharField(
        _("Currency"), max_length=12, default=get_default_currency
    )

    # Track the various amounts associated with this source
    amount_allocated = models.DecimalField(
        _("Amount Allocated"), decimal_places=2, max_digits=12, default=Decimal("0.00")
    )
    amount_debited = models.DecimalField(
        _("Amount Debited"), decimal_places=2, max_digits=12, default=Decimal("0.00")
    )
    amount_refunded = models.DecimalField(
        _("Amount Refunded"), decimal_places=2, max_digits=12, default=Decimal("0.00")
    )

    # Reference number for this payment source.  This is often used to look up
    # a transaction model for a particular payment partner.
    reference = models.CharField(_("Reference"), max_length=255, blank=True)

    # A customer-friendly label for the source, eg XXXX-XXXX-XXXX-1234
    label = models.CharField(_("Label"), max_length=128, blank=True)

    # A dictionary of submission data that is stored as part of the
    # checkout process, where we need to pass an instance of this class around
    submission_data = None

    # We keep a list of deferred transactions that are only actually saved when
    # the source is saved for the first time
    deferred_txns = None

    class Meta:
        abstract = True
        app_label = "payment"
        ordering = ["pk"]
        verbose_name = _("Source")
        verbose_name_plural = _("Sources")

    def __str__(self):
        description = _("Allocation of %(amount)s from type %(type)s") % {
            "amount": currency(self.amount_allocated, self.currency),
            "type": self.source_type,
        }
        if self.reference:
            description += _(" (reference: %s)") % self.reference
        return description

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if self.deferred_txns:
            for txn in self.deferred_txns:
                self._create_transaction(*txn)

    def create_deferred_transaction(self, txn_type, amount, reference="", status=""):
        """
        Register the data for a transaction that can't be created yet due to FK
        constraints.  This happens at checkout where create an payment source
        and a transaction but can't save them until the order model exists.
        """
        if self.deferred_txns is None:
            self.deferred_txns = []
        self.deferred_txns.append((txn_type, amount, reference, status))

    def _create_transaction(self, txn_type, amount, reference="", status=""):
        self.transactions.create(
            txn_type=txn_type, amount=amount, reference=reference, status=status
        )

    # =======
    # Actions
    # =======

    def allocate(self, amount, reference="", status=""):
        """
        Convenience method for ring-fencing money against this source
        """
        self.amount_allocated += amount
        self.save()
        self._create_transaction(
            AbstractTransaction.AUTHORISE, amount, reference, status
        )

    allocate.alters_data = True

    def debit(self, amount=None, reference="", status=""):
        """
        Convenience method for recording debits against this source
        """
        if amount is None:
            amount = self.balance
        self.amount_debited += amount
        self.save()
        self._create_transaction(AbstractTransaction.DEBIT, amount, reference, status)

    debit.alters_data = True

    def refund(self, amount, reference="", status=""):
        """
        Convenience method for recording refunds against this source
        """
        self.amount_refunded += amount
        self.save()
        self._create_transaction(AbstractTransaction.REFUND, amount, reference, status)

    refund.alters_data = True

    # ==========
    # Properties
    # ==========

    @property
    def balance(self):
        """
        Return the balance of this source
        """
        return self.amount_allocated - self.amount_debited + self.amount_refunded

    @property
    def amount_available_for_refund(self):
        """
        Return the amount available to be refunded
        """
        return self.amount_debited - self.amount_refunded


class AbstractSourceType(models.Model):
    """
    A type of payment source.

    This could be an external partner like PayPal or DataCash,
    or an internal source such as a managed account.
    """

    name = models.CharField(_("Name"), max_length=128, db_index=True)
    code = AutoSlugField(
        _("Code"),
        max_length=128,
        populate_from="name",
        unique=True,
        help_text=_("This is used within forms to identify this source type"),
    )

    class Meta:
        abstract = True
        app_label = "payment"
        ordering = ["name"]
        verbose_name = _("Source Type")
        verbose_name_plural = _("Source Types")

    def __str__(self):
        return self.name


class AbstractBankcard(models.Model):
    """
    Model representing a user's bankcard.  This is used for two purposes:

        1.  The bankcard form will return an instance of this model that can be
            used with payment gateways.  In this scenario, the instance will
            have additional attributes (start_date, issue_number, :abbr:`ccv (Card Code Verification)`) that
            payment gateways need but that we don't save.

        2.  To keep a record of a user's bankcards and allow them to be
            re-used.  This is normally done using the 'partner reference'.

    .. warning::

        Some of the fields of this model (name, expiry_date) are considered
        "cardholder data" under PCI DSS v2. Hence, if you use this model and
        store those fields then the requirements for PCI compliance will be
        more stringent.
    """

    user = models.ForeignKey(
        AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="bankcards",
        verbose_name=_("User"),
    )
    card_type = models.CharField(_("Card Type"), max_length=128)

    # Often you don't actually need the name on the bankcard
    name = models.CharField(_("Name"), max_length=255, blank=True)

    # We store an obfuscated version of the card number, just showing the last
    # 4 digits.
    number = models.CharField(_("Number"), max_length=32)

    # We store a date even though only the month is visible.  Bankcards are
    # valid until the last day of the month.
    expiry_date = models.DateField(_("Expiry Date"))

    # For payment partners who are storing the full card details for us
    partner_reference = models.CharField(
        _("Partner Reference"), max_length=255, blank=True
    )

    # Temporary data not persisted to the DB
    start_date = None
    issue_number = None
    ccv = None

    def __str__(self):
        return _("%(card_type)s %(number)s (Expires: %(expiry)s)") % {
            "card_type": self.card_type,
            "number": self.number,
            "expiry": self.expiry_month(),
        }

    def __init__(self, *args, **kwargs):
        # Pop off the temporary data
        self.start_date = kwargs.pop("start_date", None)
        self.issue_number = kwargs.pop("issue_number", None)
        self.ccv = kwargs.pop("ccv", None)
        super().__init__(*args, **kwargs)

        # Initialise the card-type
        if self.id is None:
            self.card_type = bankcards.bankcard_type(self.number)
            if self.card_type is None:
                self.card_type = "Unknown card type"

    class Meta:
        abstract = True
        app_label = "payment"
        verbose_name = _("Bankcard")
        verbose_name_plural = _("Bankcards")

    def save(self, *args, **kwargs):
        if not self.number.startswith("X"):
            self.prepare_for_save()
        super().save(*args, **kwargs)

    def prepare_for_save(self):
        # This is the first time this card instance is being saved.  We
        # remove all sensitive data
        self.number = "XXXX-XXXX-XXXX-%s" % self.number[-4:]
        self.start_date = self.issue_number = self.ccv = None

    @property
    def cvv(self):
        return self.ccv

    @property
    def obfuscated_number(self):
        return "XXXX-XXXX-XXXX-%s" % self.number[-4:]

    # pylint: disable=W0622
    def start_month(self, format="%m/%y"):
        return self.start_date.strftime(format)

    # pylint: disable=W0622
    def expiry_month(self, format="%m/%y"):
        # pylint: disable=E1101
        return self.expiry_date.strftime(format)
