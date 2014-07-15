# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):

        # Adding model 'OrderAndItemCharges'
        db.create_table('shipping_orderanditemcharges', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('code', self.gf('django.db.models.fields.SlugField')(unique=True, max_length=128, db_index=True)),
            ('name', self.gf('django.db.models.fields.CharField')(unique=True, max_length=128)),
            ('description', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('price_per_order', self.gf('django.db.models.fields.DecimalField')(default='0.00', max_digits=12, decimal_places=2)),
            ('price_per_item', self.gf('django.db.models.fields.DecimalField')(default='0.00', max_digits=12, decimal_places=2)),
            ('free_shipping_threshold', self.gf('django.db.models.fields.DecimalField')(null=True, max_digits=12, decimal_places=2, blank=True)),
        ))
        db.send_create_signal('shipping', ['OrderAndItemCharges'])

        # Adding model 'WeightBased'
        db.create_table('shipping_weightbased', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('code', self.gf('django.db.models.fields.SlugField')(unique=True, max_length=128, db_index=True)),
            ('name', self.gf('django.db.models.fields.CharField')(unique=True, max_length=128)),
            ('description', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('upper_charge', self.gf('django.db.models.fields.DecimalField')(null=True, max_digits=12, decimal_places=2)),
        ))
        db.send_create_signal('shipping', ['WeightBased'])

        # Adding model 'WeightBand'
        db.create_table('shipping_weightband', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('method', self.gf('django.db.models.fields.related.ForeignKey')(related_name='bands', to=orm['shipping.WeightBased'])),
            ('upper_limit', self.gf('django.db.models.fields.FloatField')()),
            ('charge', self.gf('django.db.models.fields.DecimalField')(max_digits=12, decimal_places=2)),
        ))
        db.send_create_signal('shipping', ['WeightBand'])


    def backwards(self, orm):

        # Deleting model 'OrderAndItemCharges'
        db.delete_table('shipping_orderanditemcharges')

        # Deleting model 'WeightBased'
        db.delete_table('shipping_weightbased')

        # Deleting model 'WeightBand'
        db.delete_table('shipping_weightband')


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
            'description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '128'}),
            'upper_charge': ('django.db.models.fields.DecimalField', [], {'null': 'True', 'max_digits': '12', 'decimal_places': '2'})
        }
    }

    complete_apps = ['shipping']
