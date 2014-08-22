# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

from oscar.core.compat import AUTH_USER_MODEL, AUTH_USER_MODEL_NAME


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'RangeProductFileUpload'
        db.create_table(u'offer_rangeproductfileupload', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('range', self.gf('django.db.models.fields.related.ForeignKey')(related_name='file_uploads', to=orm['offer.Range'])),
            ('filepath', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('size', self.gf('django.db.models.fields.PositiveIntegerField')()),
            ('uploaded_by', self.gf('django.db.models.fields.related.ForeignKey')(to=orm[AUTH_USER_MODEL])),
            ('date_uploaded', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('status', self.gf('django.db.models.fields.CharField')(default='Pending', max_length=32)),
            ('error_message', self.gf('django.db.models.fields.CharField')(max_length=255, blank=True)),
            ('date_processed', self.gf('django.db.models.fields.DateTimeField')(null=True)),
            ('num_new_skus', self.gf('django.db.models.fields.PositiveIntegerField')(null=True)),
            ('num_unknown_skus', self.gf('django.db.models.fields.PositiveIntegerField')(null=True)),
            ('num_duplicate_skus', self.gf('django.db.models.fields.PositiveIntegerField')(null=True)),
        ))
        db.send_create_signal(u'offer', ['RangeProductFileUpload'])


    def backwards(self, orm):
        # Deleting model 'RangeProductFileUpload'
        db.delete_table(u'offer_rangeproductfileupload')


    models = {
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
        'catalogue.attributeoption': {
            'Meta': {'object_name': 'AttributeOption'},
            'group': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'options'", 'to': "orm['catalogue.AttributeOptionGroup']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'option': ('django.db.models.fields.CharField', [], {'max_length': '255'})
        },
        'catalogue.attributeoptiongroup': {
            'Meta': {'object_name': 'AttributeOptionGroup'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '128'})
        },
        'catalogue.category': {
            'Meta': {'ordering': "['full_name']", 'object_name': 'Category'},
            'depth': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'full_name': ('django.db.models.fields.CharField', [], {'max_length': '255', 'db_index': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'image': ('django.db.models.fields.files.ImageField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255', 'db_index': 'True'}),
            'numchild': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'path': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '255'}),
            'slug': ('django.db.models.fields.SlugField', [], {'max_length': '255'})
        },
        'catalogue.option': {
            'Meta': {'object_name': 'Option'},
            'code': ('oscar.models.fields.autoslugfield.AutoSlugField', [], {'allow_duplicates': 'False', 'max_length': '128', 'separator': "u'-'", 'blank': 'True', 'unique': 'True', 'populate_from': "'name'", 'overwrite': 'False'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'type': ('django.db.models.fields.CharField', [], {'default': "'Required'", 'max_length': '128'})
        },
        'catalogue.product': {
            'Meta': {'ordering': "['-date_created']", 'object_name': 'Product'},
            'attributes': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['catalogue.ProductAttribute']", 'through': "orm['catalogue.ProductAttributeValue']", 'symmetrical': 'False'}),
            'categories': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['catalogue.Category']", 'through': "orm['catalogue.ProductCategory']", 'symmetrical': 'False'}),
            'date_created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'date_updated': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'db_index': 'True', 'blank': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_discountable': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'parent': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'children'", 'null': 'True', 'to': "orm['catalogue.Product']"}),
            'product_class': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'products'", 'null': 'True', 'on_delete': 'models.PROTECT', 'to': "orm['catalogue.ProductClass']"}),
            'product_options': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['catalogue.Option']", 'symmetrical': 'False', 'blank': 'True'}),
            'rating': ('django.db.models.fields.FloatField', [], {'null': 'True'}),
            'recommended_products': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['catalogue.Product']", 'symmetrical': 'False', 'through': "orm['catalogue.ProductRecommendation']", 'blank': 'True'}),
            'slug': ('django.db.models.fields.SlugField', [], {'max_length': '255'}),
            'structure': ('django.db.models.fields.CharField', [], {'default': "'standalone'", 'max_length': '10'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'upc': ('oscar.models.fields.NullCharField', [], {'max_length': '64', 'unique': 'True', 'null': 'True', 'blank': 'True'})
        },
        'catalogue.productattribute': {
            'Meta': {'ordering': "['code']", 'object_name': 'ProductAttribute'},
            'code': ('django.db.models.fields.SlugField', [], {'max_length': '128'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'option_group': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['catalogue.AttributeOptionGroup']", 'null': 'True', 'blank': 'True'}),
            'product_class': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'attributes'", 'null': 'True', 'to': "orm['catalogue.ProductClass']"}),
            'required': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'type': ('django.db.models.fields.CharField', [], {'default': "'text'", 'max_length': '20'})
        },
        'catalogue.productattributevalue': {
            'Meta': {'unique_together': "(('attribute', 'product'),)", 'object_name': 'ProductAttributeValue'},
            'attribute': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['catalogue.ProductAttribute']"}),
            'entity_content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['contenttypes.ContentType']", 'null': 'True', 'blank': 'True'}),
            'entity_object_id': ('django.db.models.fields.PositiveIntegerField', [], {'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'product': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'attribute_values'", 'to': "orm['catalogue.Product']"}),
            'value_boolean': ('django.db.models.fields.NullBooleanField', [], {'null': 'True', 'blank': 'True'}),
            'value_date': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'value_file': ('django.db.models.fields.files.FileField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'value_float': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'value_image': ('django.db.models.fields.files.ImageField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'value_integer': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'value_option': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['catalogue.AttributeOption']", 'null': 'True', 'blank': 'True'}),
            'value_richtext': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'value_text': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'})
        },
        'catalogue.productcategory': {
            'Meta': {'ordering': "['product', 'category']", 'unique_together': "(('product', 'category'),)", 'object_name': 'ProductCategory'},
            'category': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['catalogue.Category']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'product': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['catalogue.Product']"})
        },
        'catalogue.productclass': {
            'Meta': {'ordering': "['name']", 'object_name': 'ProductClass'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'options': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['catalogue.Option']", 'symmetrical': 'False', 'blank': 'True'}),
            'requires_shipping': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'slug': ('oscar.models.fields.autoslugfield.AutoSlugField', [], {'allow_duplicates': 'False', 'max_length': '128', 'separator': "u'-'", 'blank': 'True', 'unique': 'True', 'populate_from': "'name'", 'overwrite': 'False'}),
            'track_stock': ('django.db.models.fields.BooleanField', [], {'default': 'True'})
        },
        'catalogue.productrecommendation': {
            'Meta': {'ordering': "['primary', '-ranking']", 'unique_together': "(('primary', 'recommendation'),)", 'object_name': 'ProductRecommendation'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'primary': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'primary_recommendations'", 'to': "orm['catalogue.Product']"}),
            'ranking': ('django.db.models.fields.PositiveSmallIntegerField', [], {'default': '0'}),
            'recommendation': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['catalogue.Product']"})
        },
        u'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'offer.benefit': {
            'Meta': {'object_name': 'Benefit'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'max_affected_items': ('django.db.models.fields.PositiveIntegerField', [], {'null': 'True', 'blank': 'True'}),
            'proxy_class': ('oscar.models.fields.NullCharField', [], {'default': 'None', 'max_length': '255', 'unique': 'True', 'null': 'True', 'blank': 'True'}),
            'range': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['offer.Range']", 'null': 'True', 'blank': 'True'}),
            'type': ('django.db.models.fields.CharField', [], {'max_length': '128', 'blank': 'True'}),
            'value': ('oscar.models.fields.PositiveDecimalField', [], {'null': 'True', 'max_digits': '12', 'decimal_places': '2', 'blank': 'True'})
        },
        'offer.condition': {
            'Meta': {'object_name': 'Condition'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'proxy_class': ('oscar.models.fields.NullCharField', [], {'default': 'None', 'max_length': '255', 'unique': 'True', 'null': 'True', 'blank': 'True'}),
            'range': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['offer.Range']", 'null': 'True', 'blank': 'True'}),
            'type': ('django.db.models.fields.CharField', [], {'max_length': '128', 'blank': 'True'}),
            'value': ('oscar.models.fields.PositiveDecimalField', [], {'null': 'True', 'max_digits': '12', 'decimal_places': '2', 'blank': 'True'})
        },
        'offer.conditionaloffer': {
            'Meta': {'ordering': "['-priority']", 'object_name': 'ConditionalOffer'},
            'benefit': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['offer.Benefit']"}),
            'condition': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['offer.Condition']"}),
            'date_created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'end_datetime': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'max_basket_applications': ('django.db.models.fields.PositiveIntegerField', [], {'null': 'True', 'blank': 'True'}),
            'max_discount': ('django.db.models.fields.DecimalField', [], {'null': 'True', 'max_digits': '12', 'decimal_places': '2', 'blank': 'True'}),
            'max_global_applications': ('django.db.models.fields.PositiveIntegerField', [], {'null': 'True', 'blank': 'True'}),
            'max_user_applications': ('django.db.models.fields.PositiveIntegerField', [], {'null': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '128'}),
            'num_applications': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'num_orders': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'offer_type': ('django.db.models.fields.CharField', [], {'default': "'Site'", 'max_length': '128'}),
            'priority': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'redirect_url': ('oscar.models.fields.ExtendedURLField', [], {'max_length': '200', 'blank': 'True'}),
            'slug': ('oscar.models.fields.autoslugfield.AutoSlugField', [], {'allow_duplicates': 'False', 'max_length': '128', 'separator': "u'-'", 'blank': 'True', 'unique': 'True', 'populate_from': "'name'", 'overwrite': 'False'}),
            'start_datetime': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'status': ('django.db.models.fields.CharField', [], {'default': "'Open'", 'max_length': '64'}),
            'total_discount': ('django.db.models.fields.DecimalField', [], {'default': "'0.00'", 'max_digits': '12', 'decimal_places': '2'})
        },
        'offer.range': {
            'Meta': {'object_name': 'Range'},
            'classes': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "'classes'", 'blank': 'True', 'to': "orm['catalogue.ProductClass']"}),
            'date_created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'excluded_products': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "'excludes'", 'blank': 'True', 'to': "orm['catalogue.Product']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'included_categories': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "'includes'", 'blank': 'True', 'to': "orm['catalogue.Category']"}),
            'included_products': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "'includes'", 'blank': 'True', 'through': "orm['offer.RangeProduct']", 'to': "orm['catalogue.Product']"}),
            'includes_all_products': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_public': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '128'}),
            'proxy_class': ('oscar.models.fields.NullCharField', [], {'default': 'None', 'max_length': '255', 'unique': 'True', 'null': 'True', 'blank': 'True'}),
            'slug': ('oscar.models.fields.autoslugfield.AutoSlugField', [], {'allow_duplicates': 'False', 'max_length': '128', 'separator': "u'-'", 'blank': 'True', 'unique': 'True', 'populate_from': "'name'", 'overwrite': 'False'})
        },
        'offer.rangeproduct': {
            'Meta': {'unique_together': "(('range', 'product'),)", 'object_name': 'RangeProduct'},
            'display_order': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'product': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['catalogue.Product']"}),
            'range': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['offer.Range']"})
        },
        u'offer.rangeproductfileupload': {
            'Meta': {'ordering': "('-date_uploaded',)", 'object_name': 'RangeProductFileUpload'},
            'date_processed': ('django.db.models.fields.DateTimeField', [], {'null': 'True'}),
            'date_uploaded': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'error_message': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'filepath': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'num_duplicate_skus': ('django.db.models.fields.PositiveIntegerField', [], {'null': 'True'}),
            'num_new_skus': ('django.db.models.fields.PositiveIntegerField', [], {'null': 'True'}),
            'num_unknown_skus': ('django.db.models.fields.PositiveIntegerField', [], {'null': 'True'}),
            'range': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'file_uploads'", 'to': "orm['offer.Range']"}),
            'size': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'status': ('django.db.models.fields.CharField', [], {'default': "'Pending'", 'max_length': '32'}),
            'uploaded_by': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['{0}']".format(AUTH_USER_MODEL)})
        }
    }

    complete_apps = ['offer']