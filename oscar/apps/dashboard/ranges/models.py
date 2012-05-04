import datetime
import os
import csv

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
        all_skus = list(self.extract_skus())
        existing_skus = self.range.included_products.all().values_list(
            'stockrecord__partner_sku', flat=True)
        new_skus = list(set(all_skus) - set(existing_skus))

        products = Product._default_manager.filter(stockrecord__partner_sku__in=new_skus)
        for product in products:
            self.range.included_products.add(product)

        # Processing stats
        found_skus = products.values_list('stockrecord__partner_sku', flat=True)
        missing_skus = set(new_skus) - set(found_skus)
        dupes = set(all_skus).intersection(set(existing_skus))

        self.mark_as_processed(len(found_skus), len(missing_skus), len(dupes))

    def extract_skus(self):
        """
        Extract all SKU-like strings from the file
        """
        reader = csv.reader(open(self.filepath, 'r'))
        for row in reader:
            for field in row:
                yield field

    def delete_file(self):
        os.unlink(self.filepath)
