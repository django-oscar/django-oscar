# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    depends_on = (
        ('catalogue', '0001_initial'),
    )

    def forwards(self, orm):
        
        # Adding model 'PagePromotion'
        db.create_table('promotions_pagepromotion', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('content_type', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['contenttypes.ContentType'])),
            ('object_id', self.gf('django.db.models.fields.PositiveIntegerField')()),
            ('position', self.gf('django.db.models.fields.CharField')(max_length=100)),
            ('display_order', self.gf('django.db.models.fields.PositiveIntegerField')(default=0)),
            ('clicks', self.gf('django.db.models.fields.PositiveIntegerField')(default=0)),
            ('date_created', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('page_url', self.gf('oscar.models.fields.ExtendedURLField')(max_length=128, db_index=True)),
        ))
        db.send_create_signal('promotions', ['PagePromotion'])

        # Adding model 'KeywordPromotion'
        db.create_table('promotions_keywordpromotion', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('content_type', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['contenttypes.ContentType'])),
            ('object_id', self.gf('django.db.models.fields.PositiveIntegerField')()),
            ('position', self.gf('django.db.models.fields.CharField')(max_length=100)),
            ('display_order', self.gf('django.db.models.fields.PositiveIntegerField')(default=0)),
            ('clicks', self.gf('django.db.models.fields.PositiveIntegerField')(default=0)),
            ('date_created', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('keyword', self.gf('django.db.models.fields.CharField')(max_length=200)),
            ('filter', self.gf('django.db.models.fields.CharField')(max_length=200, null=True, blank=True)),
        ))
        db.send_create_signal('promotions', ['KeywordPromotion'])

        # Adding model 'RawHTML'
        db.create_table('promotions_rawhtml', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=128)),
            ('display_type', self.gf('django.db.models.fields.CharField')(max_length=128, null=True, blank=True)),
            ('body', self.gf('django.db.models.fields.TextField')()),
            ('date_created', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
        ))
        db.send_create_signal('promotions', ['RawHTML'])

        # Adding model 'Image'
        db.create_table('promotions_image', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=128)),
            ('link_url', self.gf('oscar.models.fields.ExtendedURLField')(max_length=200, null=True, blank=True)),
            ('image', self.gf('django.db.models.fields.files.ImageField')(max_length=100)),
            ('date_created', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
        ))
        db.send_create_signal('promotions', ['Image'])

        # Adding model 'MultiImage'
        db.create_table('promotions_multiimage', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=128)),
            ('date_created', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
        ))
        db.send_create_signal('promotions', ['MultiImage'])

        # Adding M2M table for field images on 'MultiImage'
        db.create_table('promotions_multiimage_images', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('multiimage', models.ForeignKey(orm['promotions.multiimage'], null=False)),
            ('image', models.ForeignKey(orm['promotions.image'], null=False))
        ))
        db.create_unique('promotions_multiimage_images', ['multiimage_id', 'image_id'])

        # Adding model 'SingleProduct'
        db.create_table('promotions_singleproduct', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=128)),
            ('product', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['catalogue.Product'])),
            ('description', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
            ('date_created', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
        ))
        db.send_create_signal('promotions', ['SingleProduct'])

        # Adding model 'HandPickedProductList'
        db.create_table('promotions_handpickedproductlist', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('description', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
            ('link_url', self.gf('oscar.models.fields.ExtendedURLField')(max_length=200, null=True, blank=True)),
            ('link_text', self.gf('django.db.models.fields.CharField')(max_length=255, null=True, blank=True)),
            ('date_created', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
        ))
        db.send_create_signal('promotions', ['HandPickedProductList'])

        # Adding model 'OrderedProduct'
        db.create_table('promotions_orderedproduct', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('list', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['promotions.HandPickedProductList'])),
            ('product', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['catalogue.Product'])),
            ('display_order', self.gf('django.db.models.fields.PositiveIntegerField')(default=0)),
        ))
        db.send_create_signal('promotions', ['OrderedProduct'])

        # Adding model 'AutomaticProductList'
        db.create_table('promotions_automaticproductlist', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('description', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
            ('link_url', self.gf('oscar.models.fields.ExtendedURLField')(max_length=200, null=True, blank=True)),
            ('link_text', self.gf('django.db.models.fields.CharField')(max_length=255, null=True, blank=True)),
            ('date_created', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('method', self.gf('django.db.models.fields.CharField')(max_length=128)),
            ('num_products', self.gf('django.db.models.fields.PositiveSmallIntegerField')(default=4)),
        ))
        db.send_create_signal('promotions', ['AutomaticProductList'])

        # Adding model 'OrderedProductList'
        db.create_table('promotions_orderedproductlist', (
            ('handpickedproductlist_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['promotions.HandPickedProductList'], unique=True, primary_key=True)),
            ('tabbed_block', self.gf('django.db.models.fields.related.ForeignKey')(related_name='tabs', to=orm['promotions.TabbedBlock'])),
            ('display_order', self.gf('django.db.models.fields.PositiveIntegerField')(default=0)),
        ))
        db.send_create_signal('promotions', ['OrderedProductList'])

        # Adding model 'TabbedBlock'
        db.create_table('promotions_tabbedblock', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('date_created', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
        ))
        db.send_create_signal('promotions', ['TabbedBlock'])


    def backwards(self, orm):
        
        # Deleting model 'PagePromotion'
        db.delete_table('promotions_pagepromotion')

        # Deleting model 'KeywordPromotion'
        db.delete_table('promotions_keywordpromotion')

        # Deleting model 'RawHTML'
        db.delete_table('promotions_rawhtml')

        # Deleting model 'Image'
        db.delete_table('promotions_image')

        # Deleting model 'MultiImage'
        db.delete_table('promotions_multiimage')

        # Removing M2M table for field images on 'MultiImage'
        db.delete_table('promotions_multiimage_images')

        # Deleting model 'SingleProduct'
        db.delete_table('promotions_singleproduct')

        # Deleting model 'HandPickedProductList'
        db.delete_table('promotions_handpickedproductlist')

        # Deleting model 'OrderedProduct'
        db.delete_table('promotions_orderedproduct')

        # Deleting model 'AutomaticProductList'
        db.delete_table('promotions_automaticproductlist')

        # Deleting model 'OrderedProductList'
        db.delete_table('promotions_orderedproductlist')

        # Deleting model 'TabbedBlock'
        db.delete_table('promotions_tabbedblock')


    models = {
        'catalogue.attributeentity': {
            'Meta': {'object_name': 'AttributeEntity'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'slug': ('django.db.models.fields.SlugField', [], {'db_index': 'True', 'max_length': '255', 'blank': 'True'}),
            'type': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'entities'", 'to': "orm['catalogue.AttributeEntityType']"})
        },
        'catalogue.attributeentitytype': {
            'Meta': {'object_name': 'AttributeEntityType'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'slug': ('django.db.models.fields.SlugField', [], {'db_index': 'True', 'max_length': '255', 'blank': 'True'})
        },
        'catalogue.attributeoption': {
            'Meta': {'object_name': 'AttributeOption'},
            'group': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'options'", 'to': "orm['catalogue.AttributeOptionGroup']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'option': ('django.db.models.fields.CharField', [], {'max_length': '255'})
        },
        'catalogue.attributeoptiongroup': {
            'Meta': {'object_name': 'AttributeOptionGroup'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '128'})
        },
        'catalogue.category': {
            'Meta': {'ordering': "['name']", 'object_name': 'Category'},
            'depth': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'full_name': ('django.db.models.fields.CharField', [], {'max_length': '1024', 'db_index': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255', 'db_index': 'True'}),
            'numchild': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'path': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '255'}),
            'slug': ('django.db.models.fields.SlugField', [], {'max_length': '1024', 'db_index': 'True'})
        },
        'catalogue.option': {
            'Meta': {'object_name': 'Option'},
            'code': ('django.db.models.fields.SlugField', [], {'max_length': '128', 'db_index': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'type': ('django.db.models.fields.CharField', [], {'default': "'Required'", 'max_length': '128'})
        },
        'catalogue.product': {
            'Meta': {'ordering': "['-date_created']", 'object_name': 'Product'},
            'attributes': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['catalogue.ProductAttribute']", 'through': "orm['catalogue.ProductAttributeValue']", 'symmetrical': 'False'}),
            'categories': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['catalogue.Category']", 'through': "orm['catalogue.ProductCategory']", 'symmetrical': 'False'}),
            'date_created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'date_updated': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'db_index': 'True', 'blank': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'parent': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'variants'", 'null': 'True', 'to': "orm['catalogue.Product']"}),
            'product_class': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['catalogue.ProductClass']", 'null': 'True'}),
            'product_options': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['catalogue.Option']", 'symmetrical': 'False', 'blank': 'True'}),
            'recommended_products': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['catalogue.Product']", 'symmetrical': 'False', 'through': "orm['catalogue.ProductRecommendation']", 'blank': 'True'}),
            'related_products': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "'relations'", 'blank': 'True', 'to': "orm['catalogue.Product']"}),
            'score': ('django.db.models.fields.FloatField', [], {'default': '0.0', 'db_index': 'True'}),
            'slug': ('django.db.models.fields.SlugField', [], {'max_length': '255', 'db_index': 'True'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'upc': ('django.db.models.fields.CharField', [], {'db_index': 'True', 'max_length': '64', 'null': 'True', 'blank': 'True'})
        },
        'catalogue.productattribute': {
            'Meta': {'ordering': "['code']", 'object_name': 'ProductAttribute'},
            'code': ('django.db.models.fields.SlugField', [], {'max_length': '128', 'db_index': 'True'}),
            'entity_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['catalogue.AttributeEntityType']", 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'option_group': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['catalogue.AttributeOptionGroup']", 'null': 'True', 'blank': 'True'}),
            'product_class': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'attributes'", 'null': 'True', 'to': "orm['catalogue.ProductClass']"}),
            'required': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'type': ('django.db.models.fields.CharField', [], {'default': "'text'", 'max_length': '20'})
        },
        'catalogue.productattributevalue': {
            'Meta': {'object_name': 'ProductAttributeValue'},
            'attribute': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['catalogue.ProductAttribute']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'product': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['catalogue.Product']"}),
            'value_boolean': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'value_date': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'value_entity': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['catalogue.AttributeEntity']", 'null': 'True', 'blank': 'True'}),
            'value_float': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'value_integer': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'value_option': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['catalogue.AttributeOption']", 'null': 'True', 'blank': 'True'}),
            'value_richtext': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'value_text': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'})
        },
        'catalogue.productcategory': {
            'Meta': {'ordering': "['-is_canonical']", 'object_name': 'ProductCategory'},
            'category': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['catalogue.Category']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_canonical': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'db_index': 'True'}),
            'product': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['catalogue.Product']"})
        },
        'catalogue.productclass': {
            'Meta': {'ordering': "['name']", 'object_name': 'ProductClass'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'options': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['catalogue.Option']", 'symmetrical': 'False', 'blank': 'True'}),
            'slug': ('django.db.models.fields.SlugField', [], {'unique': 'True', 'max_length': '128', 'db_index': 'True'})
        },
        'catalogue.productrecommendation': {
            'Meta': {'object_name': 'ProductRecommendation'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'primary': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'primary_recommendations'", 'to': "orm['catalogue.Product']"}),
            'ranking': ('django.db.models.fields.PositiveSmallIntegerField', [], {'default': '0'}),
            'recommendation': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['catalogue.Product']"})
        },
        'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'promotions.automaticproductlist': {
            'Meta': {'object_name': 'AutomaticProductList'},
            'date_created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'link_text': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'link_url': ('oscar.models.fields.ExtendedURLField', [], {'max_length': '200', 'null': 'True', 'blank': 'True'}),
            'method': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'num_products': ('django.db.models.fields.PositiveSmallIntegerField', [], {'default': '4'})
        },
        'promotions.handpickedproductlist': {
            'Meta': {'object_name': 'HandPickedProductList'},
            'date_created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'link_text': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'link_url': ('oscar.models.fields.ExtendedURLField', [], {'max_length': '200', 'null': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'products': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'to': "orm['catalogue.Product']", 'null': 'True', 'through': "orm['promotions.OrderedProduct']", 'blank': 'True'})
        },
        'promotions.image': {
            'Meta': {'object_name': 'Image'},
            'date_created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'image': ('django.db.models.fields.files.ImageField', [], {'max_length': '100'}),
            'link_url': ('oscar.models.fields.ExtendedURLField', [], {'max_length': '200', 'null': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '128'})
        },
        'promotions.keywordpromotion': {
            'Meta': {'ordering': "['-clicks']", 'object_name': 'KeywordPromotion'},
            'clicks': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
            'date_created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'display_order': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'filter': ('django.db.models.fields.CharField', [], {'max_length': '200', 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'keyword': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'object_id': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'position': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'promotions.multiimage': {
            'Meta': {'object_name': 'MultiImage'},
            'date_created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'images': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'to': "orm['promotions.Image']", 'null': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '128'})
        },
        'promotions.orderedproduct': {
            'Meta': {'ordering': "('display_order',)", 'object_name': 'OrderedProduct'},
            'display_order': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'list': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['promotions.HandPickedProductList']"}),
            'product': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['catalogue.Product']"})
        },
        'promotions.orderedproductlist': {
            'Meta': {'ordering': "('display_order',)", 'object_name': 'OrderedProductList', '_ormbases': ['promotions.HandPickedProductList']},
            'display_order': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'handpickedproductlist_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['promotions.HandPickedProductList']", 'unique': 'True', 'primary_key': 'True'}),
            'tabbed_block': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'tabs'", 'to': "orm['promotions.TabbedBlock']"})
        },
        'promotions.pagepromotion': {
            'Meta': {'ordering': "['-clicks']", 'object_name': 'PagePromotion'},
            'clicks': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
            'date_created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'display_order': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'object_id': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'page_url': ('oscar.models.fields.ExtendedURLField', [], {'max_length': '128', 'db_index': 'True'}),
            'position': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'promotions.rawhtml': {
            'Meta': {'object_name': 'RawHTML'},
            'body': ('django.db.models.fields.TextField', [], {}),
            'date_created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'display_type': ('django.db.models.fields.CharField', [], {'max_length': '128', 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '128'})
        },
        'promotions.singleproduct': {
            'Meta': {'object_name': 'SingleProduct'},
            'date_created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'product': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['catalogue.Product']"})
        },
        'promotions.tabbedblock': {
            'Meta': {'object_name': 'TabbedBlock'},
            'date_created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'})
        }
    }

    complete_apps = ['promotions']
