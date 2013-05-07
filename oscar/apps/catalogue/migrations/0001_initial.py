# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):

        # Adding model 'ProductRecommendation'
        db.create_table('catalogue_productrecommendation', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('primary', self.gf('django.db.models.fields.related.ForeignKey')(related_name='primary_recommendations', to=orm['catalogue.Product'])),
            ('recommendation', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['catalogue.Product'])),
            ('ranking', self.gf('django.db.models.fields.PositiveSmallIntegerField')(default=0)),
        ))
        db.send_create_signal('catalogue', ['ProductRecommendation'])

        # Adding model 'ProductClass'
        db.create_table('catalogue_productclass', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=128)),
            ('slug', self.gf('django.db.models.fields.SlugField')(unique=True, max_length=128, db_index=True)),
        ))
        db.send_create_signal('catalogue', ['ProductClass'])

        # Adding M2M table for field options on 'ProductClass'
        db.create_table('catalogue_productclass_options', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('productclass', models.ForeignKey(orm['catalogue.productclass'], null=False)),
            ('option', models.ForeignKey(orm['catalogue.option'], null=False))
        ))
        db.create_unique('catalogue_productclass_options', ['productclass_id', 'option_id'])

        # Adding model 'Category'
        db.create_table('catalogue_category', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('path', self.gf('django.db.models.fields.CharField')(unique=True, max_length=255)),
            ('depth', self.gf('django.db.models.fields.PositiveIntegerField')()),
            ('numchild', self.gf('django.db.models.fields.PositiveIntegerField')(default=0)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=255, db_index=True)),
            ('slug',
             self.gf('django.db.models.fields.SlugField')(max_length=255, db_index=True)),
            ('full_name',
             self.gf('django.db.models.fields.CharField')(max_length=255, db_index=True)),
        ))
        db.send_create_signal('catalogue', ['Category'])

        # Adding model 'ProductCategory'
        db.create_table('catalogue_productcategory', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('product', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['catalogue.Product'])),
            ('category', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['catalogue.Category'])),
            ('is_canonical', self.gf('django.db.models.fields.BooleanField')(default=False, db_index=True)),
        ))
        db.send_create_signal('catalogue', ['ProductCategory'])

        # Adding model 'Product'
        db.create_table('catalogue_product', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('upc', self.gf('django.db.models.fields.CharField')(db_index=True, max_length=64, null=True, blank=True)),
            ('parent', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='variants', null=True, to=orm['catalogue.Product'])),
            ('title', self.gf('django.db.models.fields.CharField')(max_length=255, null=True, blank=True)),
            ('slug', self.gf('django.db.models.fields.SlugField')(max_length=255, db_index=True)),
            ('description', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
            ('product_class', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['catalogue.ProductClass'], null=True)),
            ('score', self.gf('django.db.models.fields.FloatField')(default=0.0, db_index=True)),
            ('date_created', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('date_updated', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, db_index=True, blank=True)),
        ))
        db.send_create_signal('catalogue', ['Product'])

        # Adding M2M table for field product_options on 'Product'
        db.create_table('catalogue_product_product_options', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('product', models.ForeignKey(orm['catalogue.product'], null=False)),
            ('option', models.ForeignKey(orm['catalogue.option'], null=False))
        ))
        db.create_unique('catalogue_product_product_options', ['product_id', 'option_id'])

        # Adding M2M table for field related_products on 'Product'
        db.create_table('catalogue_product_related_products', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('from_product', models.ForeignKey(orm['catalogue.product'], null=False)),
            ('to_product', models.ForeignKey(orm['catalogue.product'], null=False))
        ))
        db.create_unique('catalogue_product_related_products', ['from_product_id', 'to_product_id'])

        # Adding model 'ContributorRole'
        db.create_table('catalogue_contributorrole', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=50)),
            ('name_plural', self.gf('django.db.models.fields.CharField')(max_length=50)),
            ('slug', self.gf('django.db.models.fields.SlugField')(max_length=50, db_index=True)),
        ))
        db.send_create_signal('catalogue', ['ContributorRole'])

        # Adding model 'Contributor'
        db.create_table('catalogue_contributor', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('slug', self.gf('django.db.models.fields.SlugField')(max_length=255, db_index=True)),
        ))
        db.send_create_signal('catalogue', ['Contributor'])

        # Adding model 'ProductContributor'
        db.create_table('catalogue_productcontributor', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('product', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['catalogue.Product'])),
            ('contributor', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['catalogue.Contributor'])),
            ('role', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['catalogue.ContributorRole'])),
        ))
        db.send_create_signal('catalogue', ['ProductContributor'])

        # Adding model 'ProductAttribute'
        db.create_table('catalogue_productattribute', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('product_class', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='attributes', null=True, to=orm['catalogue.ProductClass'])),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=128)),
            ('code', self.gf('django.db.models.fields.SlugField')(max_length=128, db_index=True)),
            ('type', self.gf('django.db.models.fields.CharField')(default='text', max_length=20)),
            ('option_group', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['catalogue.AttributeOptionGroup'], null=True, blank=True)),
            ('entity_type', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['catalogue.AttributeEntityType'], null=True, blank=True)),
            ('required', self.gf('django.db.models.fields.BooleanField')(default=False)),
        ))
        db.send_create_signal('catalogue', ['ProductAttribute'])

        # Adding model 'ProductAttributeValue'
        db.create_table('catalogue_productattributevalue', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('attribute', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['catalogue.ProductAttribute'])),
            ('product', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['catalogue.Product'])),
            ('value_text', self.gf('django.db.models.fields.CharField')(max_length=255, null=True, blank=True)),
            ('value_integer', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('value_boolean', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('value_float', self.gf('django.db.models.fields.FloatField')(null=True, blank=True)),
            ('value_richtext', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
            ('value_date', self.gf('django.db.models.fields.DateField')(null=True, blank=True)),
            ('value_option', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['catalogue.AttributeOption'], null=True, blank=True)),
            ('value_entity', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['catalogue.AttributeEntity'], null=True, blank=True)),
        ))
        db.send_create_signal('catalogue', ['ProductAttributeValue'])

        # Adding model 'AttributeOptionGroup'
        db.create_table('catalogue_attributeoptiongroup', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=128)),
        ))
        db.send_create_signal('catalogue', ['AttributeOptionGroup'])

        # Adding model 'AttributeOption'
        db.create_table('catalogue_attributeoption', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('group', self.gf('django.db.models.fields.related.ForeignKey')(related_name='options', to=orm['catalogue.AttributeOptionGroup'])),
            ('option', self.gf('django.db.models.fields.CharField')(max_length=255)),
        ))
        db.send_create_signal('catalogue', ['AttributeOption'])

        # Adding model 'AttributeEntity'
        db.create_table('catalogue_attributeentity', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('slug', self.gf('django.db.models.fields.SlugField')(db_index=True, max_length=255, blank=True)),
            ('type', self.gf('django.db.models.fields.related.ForeignKey')(related_name='entities', to=orm['catalogue.AttributeEntityType'])),
        ))
        db.send_create_signal('catalogue', ['AttributeEntity'])

        # Adding model 'AttributeEntityType'
        db.create_table('catalogue_attributeentitytype', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('slug', self.gf('django.db.models.fields.SlugField')(db_index=True, max_length=255, blank=True)),
        ))
        db.send_create_signal('catalogue', ['AttributeEntityType'])

        # Adding model 'Option'
        db.create_table('catalogue_option', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=128)),
            ('code', self.gf('django.db.models.fields.SlugField')(max_length=128, db_index=True)),
            ('type', self.gf('django.db.models.fields.CharField')(default='Required', max_length=128)),
        ))
        db.send_create_signal('catalogue', ['Option'])

        # Adding model 'ProductImage'
        db.create_table('catalogue_productimage', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('product', self.gf('django.db.models.fields.related.ForeignKey')(related_name='images', to=orm['catalogue.Product'])),
            ('original', self.gf('django.db.models.fields.files.ImageField')(max_length=100)),
            ('caption', self.gf('django.db.models.fields.CharField')(max_length=200, null=True, blank=True)),
            ('display_order', self.gf('django.db.models.fields.PositiveIntegerField')(default=0)),
            ('date_created', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
        ))
        db.send_create_signal('catalogue', ['ProductImage'])

        # Adding unique constraint on 'ProductImage', fields ['product', 'display_order']
        db.create_unique('catalogue_productimage', ['product_id', 'display_order'])


    def backwards(self, orm):

        # Removing unique constraint on 'ProductImage', fields ['product', 'display_order']
        db.delete_unique('catalogue_productimage', ['product_id', 'display_order'])

        # Deleting model 'ProductRecommendation'
        db.delete_table('catalogue_productrecommendation')

        # Deleting model 'ProductClass'
        db.delete_table('catalogue_productclass')

        # Removing M2M table for field options on 'ProductClass'
        db.delete_table('catalogue_productclass_options')

        # Deleting model 'Category'
        db.delete_table('catalogue_category')

        # Deleting model 'ProductCategory'
        db.delete_table('catalogue_productcategory')

        # Deleting model 'Product'
        db.delete_table('catalogue_product')

        # Removing M2M table for field product_options on 'Product'
        db.delete_table('catalogue_product_product_options')

        # Removing M2M table for field related_products on 'Product'
        db.delete_table('catalogue_product_related_products')

        # Deleting model 'ContributorRole'
        db.delete_table('catalogue_contributorrole')

        # Deleting model 'Contributor'
        db.delete_table('catalogue_contributor')

        # Deleting model 'ProductContributor'
        db.delete_table('catalogue_productcontributor')

        # Deleting model 'ProductAttribute'
        db.delete_table('catalogue_productattribute')

        # Deleting model 'ProductAttributeValue'
        db.delete_table('catalogue_productattributevalue')

        # Deleting model 'AttributeOptionGroup'
        db.delete_table('catalogue_attributeoptiongroup')

        # Deleting model 'AttributeOption'
        db.delete_table('catalogue_attributeoption')

        # Deleting model 'AttributeEntity'
        db.delete_table('catalogue_attributeentity')

        # Deleting model 'AttributeEntityType'
        db.delete_table('catalogue_attributeentitytype')

        # Deleting model 'Option'
        db.delete_table('catalogue_option')

        # Deleting model 'ProductImage'
        db.delete_table('catalogue_productimage')


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
            'full_name': ('django.db.models.fields.CharField', [],
                          {'max_length': '255', 'db_index': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255', 'db_index': 'True'}),
            'numchild': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'path': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '255'}),
            'slug': ('django.db.models.fields.SlugField', [], {'max_length':
                                                               '255', 'db_index': 'True'})
        },
        'catalogue.contributor': {
            'Meta': {'object_name': 'Contributor'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'slug': ('django.db.models.fields.SlugField', [], {'max_length': '255', 'db_index': 'True'})
        },
        'catalogue.contributorrole': {
            'Meta': {'object_name': 'ContributorRole'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'name_plural': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'slug': ('django.db.models.fields.SlugField', [], {'max_length': '50', 'db_index': 'True'})
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
        'catalogue.productcontributor': {
            'Meta': {'object_name': 'ProductContributor'},
            'contributor': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['catalogue.Contributor']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'product': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['catalogue.Product']"}),
            'role': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['catalogue.ContributorRole']"})
        },
        'catalogue.productimage': {
            'Meta': {'ordering': "['display_order']", 'unique_together': "(('product', 'display_order'),)", 'object_name': 'ProductImage'},
            'caption': ('django.db.models.fields.CharField', [], {'max_length': '200', 'null': 'True', 'blank': 'True'}),
            'date_created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'display_order': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'original': ('django.db.models.fields.files.ImageField', [], {'max_length': '100'}),
            'product': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'images'", 'to': "orm['catalogue.Product']"})
        },
        'catalogue.productrecommendation': {
            'Meta': {'object_name': 'ProductRecommendation'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'primary': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'primary_recommendations'", 'to': "orm['catalogue.Product']"}),
            'ranking': ('django.db.models.fields.PositiveSmallIntegerField', [], {'default': '0'}),
            'recommendation': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['catalogue.Product']"})
        }
    }

    complete_apps = ['catalogue']
