# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

from oscar.core.compat import AUTH_USER_MODEL, AUTH_USER_MODEL_NAME


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Deleting model 'RangeProductFileUpload'
        db.delete_table(u'ranges_rangeproductfileupload')


    def backwards(self, orm):
        # Adding model 'RangeProductFileUpload'
        db.create_table(u'ranges_rangeproductfileupload', (
            ('status', self.gf('django.db.models.fields.CharField')(default='Pending', max_length=32)),
            ('date_processed', self.gf('django.db.models.fields.DateTimeField')(null=True)),
            ('uploaded_by', self.gf('django.db.models.fields.related.ForeignKey')(to=orm[AUTH_USER_MODEL])),
            ('num_new_skus', self.gf('django.db.models.fields.PositiveIntegerField')(null=True)),
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('size', self.gf('django.db.models.fields.PositiveIntegerField')()),
            ('filepath', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('error_message', self.gf('django.db.models.fields.CharField')(max_length=255, blank=True)),
            ('num_unknown_skus', self.gf('django.db.models.fields.PositiveIntegerField')(null=True)),
            ('range', self.gf('django.db.models.fields.related.ForeignKey')(related_name='file_uploads', to=orm['offer.Range'])),
            ('num_duplicate_skus', self.gf('django.db.models.fields.PositiveIntegerField')(null=True)),
            ('date_uploaded', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
        ))
        db.send_create_signal('ranges', ['RangeProductFileUpload'])


    models = {
        
    }

    complete_apps = ['ranges']