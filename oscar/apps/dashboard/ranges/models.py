import os
import re
from django.utils.translation import ugettext_lazy as _
from django.db import models
from django.utils.timezone import now
from oscar.core.compat import AUTH_USER_MODEL
from six.moves import filter

Product = models.get_model('catalogue', 'Product')


class RangeProductFileUpload(models.Model):
    range = models.ForeignKey('offer.Range', related_name='file_uploads',
                              verbose_name=_("Range"))
    filepath = models.CharField(_("File Path"), max_length=255)
    size = models.PositiveIntegerField(_("Size"))
    uploaded_by = models.ForeignKey(AUTH_USER_MODEL,
                                    verbose_name=_("Uploaded By"))
    date_uploaded = models.DateTimeField(_("Date Uploaded"), auto_now_add=True)

    PENDING, FAILED, PROCESSED = 'Pending', 'Failed', 'Processed'
    choices = (
        (PENDING, PENDING),
        (FAILED, FAILED),
        (PROCESSED, PROCESSED),
    )
    status = models.CharField(_("Status"), max_length=32, choices=choices,
                              default=PENDING)
    error_message = models.CharField(_("Error Message"), max_length=255,
                                     blank=True)

    # Post-processing audit fields
    date_processed = models.DateTimeField(_("Date Processed"), null=True)
    num_new_skus = models.PositiveIntegerField(_("Number of New SKUs"),
                                               null=True)
    num_unknown_skus = models.PositiveIntegerField(_("Number of Unknown SKUs"),
                                                   null=True)
    num_duplicate_skus = models.PositiveIntegerField(
        _("Number of Duplicate SKUs"), null=True)

    class Meta:
        ordering = ('-date_uploaded',)
        verbose_name = _("Range Product Uploaded File")
        verbose_name_plural = _("Range Product Uploaded Files")

    @property
    def filename(self):
        return os.path.basename(self.filepath)

    def mark_as_failed(self, message=None):
        self.date_processed = now()
        self.error_message = message
        self.status = self.FAILED
        self.save()

    def mark_as_processed(self, num_new, num_unknown, num_duplicate):
        self.status = self.PROCESSED
        self.date_processed = now()
        self.num_new_skus = num_new
        self.num_unknown_skus = num_unknown
        self.num_duplicate_skus = num_duplicate
        self.save()

    def was_processing_successful(self):
        return self.status == self.PROCESSED

    def process(self):
        """
        Process the file upload and add products to the range
        """
        all_ids = set(self.extract_ids())
        products = self.range.included_products.all()
        existing_skus = products.values_list('stockrecord__partner_sku',
                                             flat=True)
        existing_skus = set(filter(bool, existing_skus))
        existing_upcs = products.values_list('upc', flat=True)
        existing_upcs = set(filter(bool, existing_upcs))
        existing_ids = existing_skus.union(existing_upcs)
        new_ids = all_ids - existing_ids

        products = Product._default_manager.filter(
            models.Q(stockrecord__partner_sku__in=new_ids) |
            models.Q(upc__in=new_ids))
        for product in products:
            self.range.add_product(product)

        # Processing stats
        found_skus = products.values_list('stockrecord__partner_sku',
                                          flat=True)
        found_skus = set(filter(bool, found_skus))
        found_upcs = set(filter(bool, products.values_list('upc', flat=True)))
        found_ids = found_skus.union(found_upcs)
        missing_ids = new_ids - found_ids
        dupes = set(all_ids).intersection(existing_ids)

        self.mark_as_processed(products.count(), len(missing_ids), len(dupes))

    def extract_ids(self):
        """
        Extract all SKU- or UPC-like strings from the file
        """
        for line in open(self.filepath, 'r'):
            for id in re.split('[^\w:\.-]', line):
                if id:
                    yield id

    def delete_file(self):
        os.unlink(self.filepath)
