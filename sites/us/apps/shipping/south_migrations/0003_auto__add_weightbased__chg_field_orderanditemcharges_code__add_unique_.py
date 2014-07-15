# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Adding model 'WeightBased'
        db.create_table('shipping_weightbased', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('code', self.gf('django.db.models.fields.SlugField')(unique=True, max_length=128, db_index=True)),
            ('name', self.gf('django.db.models.fields.CharField')(unique=True, max_length=128)),
            ('description', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('upper_charge', self.gf('django.db.models.fields.DecimalField')(null=True, max_digits=12, decimal_places=2)),
        ))
        db.send_create_signal('shipping', ['WeightBased'])

        # Changing field 'OrderAndItemCharges.code'
        db.alter_column('shipping_orderanditemcharges', 'code', self.gf('django.db.models.fields.SlugField')(unique=True, max_length=128))

        # Adding index on 'OrderAndItemCharges', fields ['code']
        db.create_index('shipping_orderanditemcharges', ['code'])

        # Adding unique constraint on 'OrderAndItemCharges', fields ['name']
        db.create_unique('shipping_orderanditemcharges', ['name'])

        # Deleting field 'WeightBand.method_code'
        db.delete_column('shipping_weightband', 'method_code')

        # Adding field 'WeightBand.method'
        db.add_column('shipping_weightband', 'method',
                      self.gf('django.db.models.fields.related.ForeignKey')(default=1, related_name='bands', to=orm['shipping.WeightBased']), keep_default=False)


    def backwards(self, orm):
        
        # Removing unique constraint on 'OrderAndItemCharges', fields ['name']
        db.delete_unique('shipping_orderanditemcharges', ['name'])

        # Removing index on 'OrderAndItemCharges', fields ['code']
        db.delete_index('shipping_orderanditemcharges', ['code'])

        # Deleting model 'WeightBased'
        db.delete_table('shipping_weightbased')

        # Changing field 'OrderAndItemCharges.code'
        db.alter_column('shipping_orderanditemcharges', 'code', self.gf('django.db.models.fields.CharField')(max_length=128, unique=True))

        # User chose to not deal with backwards NULL issues for 'WeightBand.method_code'
        raise RuntimeError("Cannot reverse this migration. 'WeightBand.method_code' and its values cannot be restored.")

        # Deleting field 'WeightBand.method'
        db.delete_column('shipping_weightband', 'method_id')


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
