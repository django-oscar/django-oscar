# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

from oscar.core.compat import AUTH_USER_MODEL, AUTH_USER_MODEL_NAME


class Migration(SchemaMigration):

    def forwards(self, orm):

        # Changing field 'UserAddress.first_name'
        db.alter_column(u'address_useraddress', 'first_name', self.gf('django.db.models.fields.CharField')(default='', max_length=255))

        # Changing field 'UserAddress.title'
        db.alter_column(u'address_useraddress', 'title', self.gf('django.db.models.fields.CharField')(default='', max_length=64))

        # Changing field 'UserAddress.notes'
        db.alter_column(u'address_useraddress', 'notes', self.gf('django.db.models.fields.TextField')(default=''))

        # Changing field 'UserAddress.line4'
        db.alter_column(u'address_useraddress', 'line4', self.gf('django.db.models.fields.CharField')(default='', max_length=255))

        # Changing field 'UserAddress.line3'
        db.alter_column(u'address_useraddress', 'line3', self.gf('django.db.models.fields.CharField')(default='', max_length=255))

        # Changing field 'UserAddress.line2'
        db.alter_column(u'address_useraddress', 'line2', self.gf('django.db.models.fields.CharField')(default='', max_length=255))

        # Changing field 'UserAddress.state'
        db.alter_column(u'address_useraddress', 'state', self.gf('django.db.models.fields.CharField')(default='', max_length=255))

        # Changing field 'UserAddress.postcode'
        db.alter_column(u'address_useraddress', 'postcode', self.gf('oscar.models.fields.UppercaseCharField')(default='', max_length=64))

        # Changing field 'Country.iso_3166_1_a3'
        db.alter_column(u'address_country', 'iso_3166_1_a3', self.gf('django.db.models.fields.CharField')(default='', max_length=3))

    def backwards(self, orm):

        # Changing field 'UserAddress.first_name'
        db.alter_column(u'address_useraddress', 'first_name', self.gf('django.db.models.fields.CharField')(max_length=255, null=True))

        # Changing field 'UserAddress.title'
        db.alter_column(u'address_useraddress', 'title', self.gf('django.db.models.fields.CharField')(max_length=64, null=True))

        # Changing field 'UserAddress.notes'
        db.alter_column(u'address_useraddress', 'notes', self.gf('django.db.models.fields.TextField')(null=True))

        # Changing field 'UserAddress.line4'
        db.alter_column(u'address_useraddress', 'line4', self.gf('django.db.models.fields.CharField')(max_length=255, null=True))

        # Changing field 'UserAddress.line3'
        db.alter_column(u'address_useraddress', 'line3', self.gf('django.db.models.fields.CharField')(max_length=255, null=True))

        # Changing field 'UserAddress.line2'
        db.alter_column(u'address_useraddress', 'line2', self.gf('django.db.models.fields.CharField')(max_length=255, null=True))

        # Changing field 'UserAddress.state'
        db.alter_column(u'address_useraddress', 'state', self.gf('django.db.models.fields.CharField')(max_length=255, null=True))

        # Changing field 'UserAddress.postcode'
        db.alter_column(u'address_useraddress', 'postcode', self.gf('oscar.models.fields.UppercaseCharField')(max_length=64, null=True))

        # Changing field 'Country.iso_3166_1_a3'
        db.alter_column(u'address_country', 'iso_3166_1_a3', self.gf('django.db.models.fields.CharField')(max_length=3, null=True))

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
        u'address.useraddress': {
            'Meta': {'ordering': "['-num_orders']", 'unique_together': "(('user', 'hash'),)", 'object_name': 'UserAddress'},
            'country': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['address.Country']"}),
            'date_created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'hash': ('django.db.models.fields.CharField', [], {'max_length': '255', 'db_index': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_default_for_billing': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_default_for_shipping': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'line1': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'line2': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'line3': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'line4': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'notes': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'num_orders': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'phone_number': ('oscar.models.fields.PhoneNumberField', [], {'max_length': '128', 'blank': 'True'}),
            'postcode': ('oscar.models.fields.UppercaseCharField', [], {'max_length': '64', 'blank': 'True'}),
            'search_text': ('django.db.models.fields.CharField', [], {'max_length': '1000'}),
            'state': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '64', 'blank': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'addresses'", 'to': u"orm['{0}']".format(AUTH_USER_MODEL)})
        },
        u'auth.group': {
            'Meta': {'object_name': 'Group'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '80'}),
            'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'})
        },
        u'auth.permission': {
            'Meta': {'ordering': "(u'content_type__app_label', u'content_type__model', u'codename')", 'unique_together': "((u'content_type', u'codename'),)", 'object_name': 'Permission'},
            'codename': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['contenttypes.ContentType']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        AUTH_USER_MODEL: {
            'Meta': {'object_name': AUTH_USER_MODEL_NAME},
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "u'user_set'", 'blank': 'True', 'to': u"orm['auth.Group']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "u'user_set'", 'blank': 'True', 'to': u"orm['auth.Permission']"}),
            'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30'})
        },
        u'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        }
    }

    complete_apps = ['address']