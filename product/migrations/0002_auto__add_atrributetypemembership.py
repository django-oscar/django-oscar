# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):
    
    def forwards(self, orm):
        
        # Adding model 'AtrributeTypeMembership'
        db.create_table('product_atrributetypemembership', (
            ('attribute_Type', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['product.AttributeType'])),
            ('type', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['product.Type'])),
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('relation_type', self.gf('django.db.models.fields.CharField')(default='optional', max_length=16)),
        ))
        db.send_create_signal('product', ['AtrributeTypeMembership'])
    
    
    def backwards(self, orm):
        
        # Deleting model 'AtrributeTypeMembership'
        db.delete_table('product_atrributetypemembership')
    
    
    models = {
        'product.atrributetypemembership': {
            'Meta': {'object_name': 'AtrributeTypeMembership'},
            'attribute_Type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['product.AttributeType']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'relation_type': ('django.db.models.fields.CharField', [], {'default': "'optional'", 'max_length': '16'}),
            'type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['product.Type']"})
        },
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
