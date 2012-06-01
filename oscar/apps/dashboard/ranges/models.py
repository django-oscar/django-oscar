import datetime
import os
import re

from django.db import models
Product = models.get_model('catalogue', 'Product')


class RangeProductFileUpload(models.Model):
    range = models.ForeignKey('offer.Range', related_name='file_uploads')
    filepath = models.CharField(max_length=255)
    size = models.PositiveIntegerField()
    uploaded_by = models.ForeignKey('auth.User')
    date_uploaded = models.DateTimeField(auto_now_add=True)

    PENDING, FAILED, PROCESSED = 'Pending', 'Failed', 'Processed'
    choices = (
        (PENDING, PENDING),
        (FAILED, FAILED),
        (PROCESSED, PROCESSED),
    )
    status = models.CharField(max_length=32, choices=choices, default=PENDING)
    error_message = models.CharField(max_length=255, null=True)

    # Post-processing audit fields
    date_processed = models.DateTimeField(null=True)
    num_new_skus = models.PositiveIntegerField(null=True)
    num_unknown_skus = models.PositiveIntegerField(null=True)
    num_duplicate_skus = models.PositiveIntegerField(null=True)

    class Meta:
        ordering = ('-date_uploaded',)

    @property
    def filename(self):
        return os.path.basename(self.filepath)

    def mark_as_failed(self, message=None):
        self.date_processed = datetime.datetime.now()
        self.error_message = message
        self.status = self.FAILED
        self.save()

    def mark_as_processed(self, num_new, num_unknown, num_duplicate):
        self.status = self.PROCESSED
        self.date_processed = datetime.datetime.now()
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
        existing_skus = set(filter(bool, products.values_list('stockrecord__partner_sku', flat=True)))
        existing_upcs = set(filter(bool, products.values_list('upc', flat=True)))
        existing_ids = existing_skus.union(existing_upcs)
        new_ids = all_ids - existing_ids

        products = Product._default_manager.filter(
            models.Q(stockrecord__partner_sku__in=new_ids) |
            models.Q(upc__in=new_ids))
        for product in products:
            self.range.included_products.add(product)

        # Processing stats
        found_skus = set(filter(bool, products.values_list('stockrecord__partner_sku', flat=True)))
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
