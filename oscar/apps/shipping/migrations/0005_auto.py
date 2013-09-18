# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    depends_on = (
        ('address', '0001_initial'),
    )

    def forwards(self, orm):
        # Adding M2M table for field countries on 'OrderAndItemCharges'
        db.create_table('shipping_orderanditemcharges_countries', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('orderanditemcharges', models.ForeignKey(orm['shipping.orderanditemcharges'], null=False)),
            ('country', models.ForeignKey(orm['address.country'], null=False))
        ))
        db.create_unique('shipping_orderanditemcharges_countries', ['orderanditemcharges_id', 'country_id'])

        # Adding M2M table for field countries on 'WeightBased'
        db.create_table('shipping_weightbased_countries', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('weightbased', models.ForeignKey(orm['shipping.weightbased'], null=False)),
            ('country', models.ForeignKey(orm['address.country'], null=False))
        ))
        db.create_unique('shipping_weightbased_countries', ['weightbased_id', 'country_id'])


    def backwards(self, orm):
        # Removing M2M table for field countries on 'OrderAndItemCharges'
        db.delete_table('shipping_orderanditemcharges_countries')

        # Removing M2M table for field countries on 'WeightBased'
        db.delete_table('shipping_weightbased_countries')


    models = {
        'address.country': {
            'Meta': {'ordering': "('-is_highlighted', 'name')", 'object_name': 'Country'},
            'is_highlighted': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'db_index': 'True'}),
            'is_shipping_country': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'db_index': 'True'}),
            'iso_3166_1_a2': ('django.db.models.fields.CharField', [], {'max_length': '2', 'primary_key': 'True'}),
            'iso_3166_1_a3': ('django.db.models.fields.CharField', [], {'max_length': '3', 'null': 'True', 'db_index': 'True'}),
            'iso_3166_1_numeric': ('django.db.models.fields.PositiveSmallIntegerField', [], {'null': 'True', 'db_index': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'printable_name': ('django.db.models.fields.CharField', [], {'max_length': '128'})
        },
        'shipping.orderanditemcharges': {
            'Meta': {'object_name': 'OrderAndItemCharges'},
            'code': ('django.db.models.fields.SlugField', [], {'unique': 'True', 'max_length': '128'}),
            'countries': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'to': "orm['address.Country']", 'null': 'True', 'blank': 'True'}),
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
            'code': ('django.db.models.fields.SlugField', [], {'unique': 'True', 'max_length': '128'}),
            'countries': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'to': "orm['address.Country']", 'null': 'True', 'blank': 'True'}),
            'default_weight': ('django.db.models.fields.DecimalField', [], {'default': "'0.00'", 'max_digits': '12', 'decimal_places': '2'}),
            'description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '128'}),
            'upper_charge': ('django.db.models.fields.DecimalField', [], {'null': 'True', 'max_digits': '12', 'decimal_places': '2'})
        }
    }

    complete_apps = ['shipping']
