# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Adding model 'OrderAndItemLevelChargeMethod'
        db.create_table('shipping_orderanditemlevelchargemethod', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('code', self.gf('django.db.models.fields.CharField')(unique=True, max_length=128)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=128)),
            ('description', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('price_currency', self.gf('django.db.models.fields.CharField')(default='GBP', max_length=12)),
            ('price_per_order', self.gf('django.db.models.fields.DecimalField')(default='0.00', max_digits=12, decimal_places=2)),
            ('price_per_item', self.gf('django.db.models.fields.DecimalField')(default='0.00', max_digits=12, decimal_places=2)),
            ('free_shipping_threshold', self.gf('django.db.models.fields.DecimalField')(null=True, max_digits=12, decimal_places=2, blank=True)),
        ))
        db.send_create_signal('shipping', ['OrderAndItemLevelChargeMethod'])


    def backwards(self, orm):
        
        # Deleting model 'OrderAndItemLevelChargeMethod'
        db.delete_table('shipping_orderanditemlevelchargemethod')


    models = {
        'shipping.orderanditemlevelchargemethod': {
            'Meta': {'object_name': 'OrderAndItemLevelChargeMethod'},
            'code': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '128'}),
            'description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'free_shipping_threshold': ('django.db.models.fields.DecimalField', [], {'null': 'True', 'max_digits': '12', 'decimal_places': '2', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'price_currency': ('django.db.models.fields.CharField', [], {'default': "'GBP'", 'max_length': '12'}),
            'price_per_item': ('django.db.models.fields.DecimalField', [], {'default': "'0.00'", 'max_digits': '12', 'decimal_places': '2'}),
            'price_per_order': ('django.db.models.fields.DecimalField', [], {'default': "'0.00'", 'max_digits': '12', 'decimal_places': '2'})
        }
    }

    complete_apps = ['shipping']
