# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):

        # Adding field 'WeightBased.default_weight'
        db.add_column('shipping_weightbased', 'default_weight', self.gf('django.db.models.fields.DecimalField')(default='0.00', max_digits=12, decimal_places=2), keep_default=False)


    def backwards(self, orm):

        # Deleting field 'WeightBased.default_weight'
        db.delete_column('shipping_weightbased', 'default_weight')


    models = {
        'shipping.orderanditemcharges': {
            'Meta': {'object_name': 'OrderAndItemCharges'},
            'code': ('django.db.models.fields.SlugField', [], {'unique': 'True', 'max_length': '128', 'db_index': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'free_shipping_threshold': ('django.db.models.fields.DecimalField', [], {'null': 'True', 'max_digits': '12', 'decimal_places': '2', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '128'}),
            'price_per_item': ('django.db.models.fields.DecimalField', [], {'default': "'0.00'", 'max_digits': '12', 'decimal_places': '2'}),
            'price_per_order': ('django.db.models.fields.DecimalField', [], {'default': "'0.00'", 'max_digits': '12', 'decimal_places': '2'})
        },
        'shipping.weightband': {
            'Meta': {'ordering': "['upper_limit']", 'object_name': 'WeightBand'},
            'charge': ('django.db.models.fields.DecimalField', [], {'max_digits': '12', 'decimal_places': '2'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'method': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'bands'", 'to': "orm['shipping.WeightBased']"}),
            'upper_limit': ('django.db.models.fields.FloatField', [], {})
        },
        'shipping.weightbased': {
            'Meta': {'object_name': 'WeightBased'},
            'code': ('django.db.models.fields.SlugField', [], {'unique': 'True', 'max_length': '128', 'db_index': 'True'}),
            'default_weight': ('django.db.models.fields.DecimalField', [], {'default': "'0.00'", 'max_digits': '12', 'decimal_places': '2'}),
            'description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '128'}),
            'upper_charge': ('django.db.models.fields.DecimalField', [], {'null': 'True', 'max_digits': '12', 'decimal_places': '2'})
        }
    }

    complete_apps = ['shipping']
