# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):
    
    def forwards(self, orm):
        
        # Adding model 'AttributeType'
        db.create_table('product_attributetype', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=128)),
        ))
        db.send_create_signal('product', ['AttributeType'])

        # Adding model 'Type'
        db.create_table('product_type', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=128)),
        ))
        db.send_create_signal('product', ['Type'])

        # Adding M2M table for field attribute_types on 'Type'
        db.create_table('product_type_attribute_types', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('type', models.ForeignKey(orm['product.type'], null=False)),
            ('attributetype', models.ForeignKey(orm['product.attributetype'], null=False))
        ))
        db.create_unique('product_type_attribute_types', ['type_id', 'attributetype_id'])

        # Adding model 'Item'
        db.create_table('product_item', (
            ('name', self.gf('django.db.models.fields.CharField')(max_length=128)),
            ('partner_id', self.gf('django.db.models.fields.CharField')(max_length=32)),
            ('date_available', self.gf('django.db.models.fields.DateField')()),
            ('date_created', self.gf('django.db.models.fields.DateTimeField')()),
            ('type', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['product.Type'])),
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
        ))
        db.send_create_signal('product', ['Item'])

        # Adding model 'Attribute'
        db.create_table('product_attribute', (
            ('attribute_type', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['product.AttributeType'])),
            ('product', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['product.Item'])),
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('value', self.gf('django.db.models.fields.CharField')(max_length=256)),
        ))
        db.send_create_signal('product', ['Attribute'])

        # Adding model 'StockRecord'
        db.create_table('product_stockrecord', (
            ('tax', self.gf('django.db.models.fields.FloatField')()),
            ('product', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['product.Item'])),
            ('price_excl_tax', self.gf('django.db.models.fields.FloatField')()),
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
        ))
        db.send_create_signal('product', ['StockRecord'])
    
    
    def backwards(self, orm):
        
        # Deleting model 'AttributeType'
        db.delete_table('product_attributetype')

        # Deleting model 'Type'
        db.delete_table('product_type')

        # Removing M2M table for field attribute_types on 'Type'
        db.delete_table('product_type_attribute_types')

        # Deleting model 'Item'
        db.delete_table('product_item')

        # Deleting model 'Attribute'
        db.delete_table('product_attribute')

        # Deleting model 'StockRecord'
        db.delete_table('product_stockrecord')
    
    
    models = {
        'product.attribute': {
            'Meta': {'object_name': 'Attribute'},
            'attribute_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['product.AttributeType']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'product': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['product.Item']"}),
            'value': ('django.db.models.fields.CharField', [], {'max_length': '256'})
        },
        'product.attributetype': {
            'Meta': {'object_name': 'AttributeType'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '128'})
        },
        'product.item': {
            'Meta': {'object_name': 'Item'},
            'date_available': ('django.db.models.fields.DateField', [], {}),
            'date_created': ('django.db.models.fields.DateTimeField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'partner_id': ('django.db.models.fields.CharField', [], {'max_length': '32'}),
            'type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['product.Type']"})
        },
        'product.stockrecord': {
            'Meta': {'object_name': 'StockRecord'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'price_excl_tax': ('django.db.models.fields.FloatField', [], {}),
            'product': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['product.Item']"}),
            'tax': ('django.db.models.fields.FloatField', [], {})
        },
        'product.type': {
            'Meta': {'object_name': 'Type'},
            'attribute_types': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['product.AttributeType']", 'symmetrical': 'False'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '128'})
        }
    }
    
    complete_apps = ['product']
