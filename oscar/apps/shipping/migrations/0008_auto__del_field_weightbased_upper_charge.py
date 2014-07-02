# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Deleting field 'WeightBased.upper_charge'
        db.delete_column(u'shipping_weightbased', 'upper_charge')


    def backwards(self, orm):
        # Adding field 'WeightBased.upper_charge'
        db.add_column(u'shipping_weightbased', 'upper_charge',
                      self.gf('django.db.models.fields.DecimalField')(null=True, max_digits=12, decimal_places=2),
                      keep_default=False)


    models = {
        u'address.country': {
            'Meta': {'ordering': "('-display_order', 'name')", 'object_name': 'Country'},
            'display_order': ('django.db.models.fields.PositiveSmallIntegerField', [], {'default': '0', 'db_index': 'True'}),
            'is_shipping_country': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'db_index': 'True'}),
            'iso_3166_1_a2': ('django.db.models.fields.CharField', [], {'max_length': '2', 'primary_key': 'True'}),
            'iso_3166_1_a3': ('django.db.models.fields.CharField', [], {'db_index': 'True', 'max_length': '3', 'blank': 'True'}),
            'iso_3166_1_numeric': ('django.db.models.fields.PositiveSmallIntegerField', [], {'null': 'True', 'db_index': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'printable_name': ('django.db.models.fields.CharField', [], {'max_length': '128'})
        },
        u'shipping.orderanditemcharges': {
            'Meta': {'ordering': "['name']", 'object_name': 'OrderAndItemCharges'},
            'code': ('oscar.models.fields.autoslugfield.AutoSlugField', [], {'allow_duplicates': 'False', 'max_length': '128', 'separator': "u'-'", 'blank': 'True', 'unique': 'True', 'populate_from': "'name'", 'overwrite': 'False'}),
            'countries': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'to': u"orm['address.Country']", 'null': 'True', 'blank': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'free_shipping_threshold': ('django.db.models.fields.DecimalField', [], {'null': 'True', 'max_digits': '12', 'decimal_places': '2', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '128'}),
            'price_per_item': ('django.db.models.fields.DecimalField', [], {'default': "'0.00'", 'max_digits': '12', 'decimal_places': '2'}),
            'price_per_order': ('django.db.models.fields.DecimalField', [], {'default': "'0.00'", 'max_digits': '12', 'decimal_places': '2'})
        },
        u'shipping.weightband': {
            'Meta': {'ordering': "['method', 'upper_limit']", 'object_name': 'WeightBand'},
            'charge': ('django.db.models.fields.DecimalField', [], {'max_digits': '12', 'decimal_places': '2'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'method': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'bands'", 'to': u"orm['shipping.WeightBased']"}),
            'upper_limit': ('django.db.models.fields.DecimalField', [], {'max_digits': '12', 'decimal_places': '3'})
        },
        u'shipping.weightbased': {
            'Meta': {'ordering': "['name']", 'object_name': 'WeightBased'},
            'code': ('oscar.models.fields.autoslugfield.AutoSlugField', [], {'allow_duplicates': 'False', 'max_length': '128', 'separator': "u'-'", 'blank': 'True', 'unique': 'True', 'populate_from': "'name'", 'overwrite': 'False'}),
            'countries': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'to': u"orm['address.Country']", 'null': 'True', 'blank': 'True'}),
            'default_weight': ('django.db.models.fields.DecimalField', [], {'default': "'0.000'", 'max_digits': '12', 'decimal_places': '3'}),
            'description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '128'})
        }
    }

    complete_apps = ['shipping']