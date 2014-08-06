# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import oscar.models.fields
import django.core.validators
import django.db.models.deletion
import oscar.models.fields.autoslugfield


class Migration(migrations.Migration):

    dependencies = [
        ('contenttypes', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='AttributeOption',
            fields=[
                ('id', models.AutoField(auto_created=True, verbose_name='ID', primary_key=True, serialize=False)),
                ('option', models.CharField(verbose_name='Option', max_length=255)),
            ],
            options={
                'verbose_name': 'Attribute option',
                'verbose_name_plural': 'Attribute options',
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='AttributeOptionGroup',
            fields=[
                ('id', models.AutoField(auto_created=True, verbose_name='ID', primary_key=True, serialize=False)),
                ('name', models.CharField(verbose_name='Name', max_length=128)),
            ],
            options={
                'verbose_name': 'Attribute option group',
                'verbose_name_plural': 'Attribute option groups',
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.AddField(
            model_name='attributeoption',
            name='group',
            field=models.ForeignKey(verbose_name='Group', to='catalogue.AttributeOptionGroup'),
            preserve_default=True,
        ),
        migrations.CreateModel(
            name='Category',
            fields=[
                ('id', models.AutoField(auto_created=True, verbose_name='ID', primary_key=True, serialize=False)),
                ('path', models.CharField(unique=True, max_length=255)),
                ('depth', models.PositiveIntegerField()),
                ('numchild', models.PositiveIntegerField(default=0)),
                ('name', models.CharField(verbose_name='Name', db_index=True, max_length=255)),
                ('description', models.TextField(verbose_name='Description', blank=True)),
                ('image', models.ImageField(verbose_name='Image', upload_to='categories', blank=True, null=True, max_length=255)),
                ('slug', models.SlugField(editable=False, verbose_name='Slug', max_length=255)),
                ('full_name', models.CharField(editable=False, verbose_name='Full Name', db_index=True, max_length=255)),
            ],
            options={
                'verbose_name': 'Category',
                'verbose_name_plural': 'Categories',
                'ordering': ['full_name'],
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Option',
            fields=[
                ('id', models.AutoField(auto_created=True, verbose_name='ID', primary_key=True, serialize=False)),
                ('name', models.CharField(verbose_name='Name', max_length=128)),
                ('code', oscar.models.fields.autoslugfield.AutoSlugField(editable=False, verbose_name='Code', blank=True, max_length=128, populate_from='name', unique=True)),
                ('type', models.CharField(verbose_name='Status', choices=[('Required', 'Required - a value for this option must be specified'), ('Optional', 'Optional - a value for this option can be omitted')], default='Required', max_length=128)),
            ],
            options={
                'verbose_name': 'Option',
                'verbose_name_plural': 'Options',
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Product',
            fields=[
                ('id', models.AutoField(auto_created=True, verbose_name='ID', primary_key=True, serialize=False)),
                ('structure', models.CharField(verbose_name='Product structure', choices=[('standalone', 'Stand-alone product'), ('parent', 'Parent product'), ('child', 'Child product')], default='standalone', max_length=10)),
                ('upc', oscar.models.fields.NullCharField(verbose_name='UPC', max_length=64, help_text='Universal Product Code (UPC) is an identifier for a product which is not specific to a particular  supplier. Eg an ISBN for a book.', unique=True)),
                ('title', models.CharField(verbose_name='Title', blank=True, max_length=255)),
                ('slug', models.SlugField(verbose_name='Slug', max_length=255)),
                ('description', models.TextField(verbose_name='Description', blank=True)),
                ('rating', models.FloatField(editable=False, verbose_name='Rating', null=True)),
                ('date_created', models.DateTimeField(verbose_name='Date created', auto_now_add=True)),
                ('date_updated', models.DateTimeField(verbose_name='Date updated', auto_now=True, db_index=True)),
                ('is_discountable', models.BooleanField(verbose_name='Is discountable?', help_text='This flag indicates if this product can be used in an offer or not', default=True)),
                ('parent', models.ForeignKey(verbose_name='Parent product', blank=True, help_text="Only choose a parent product if you're creating a child product.  For example if this is a size 4 of a particular t-shirt.  Leave blank if this is a stand-alone product (i.e. there is only one version of this product).", to='catalogue.Product', null=True)),
                ('product_options', models.ManyToManyField(verbose_name='Product Options', blank=True, to='catalogue.Option')),
            ],
            options={
                'verbose_name': 'Product',
                'verbose_name_plural': 'Products',
                'ordering': ['-date_created'],
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='ProductAttribute',
            fields=[
                ('id', models.AutoField(auto_created=True, verbose_name='ID', primary_key=True, serialize=False)),
                ('name', models.CharField(verbose_name='Name', max_length=128)),
                ('code', models.SlugField(verbose_name='Code', validators=[django.core.validators.RegexValidator(regex='^[a-zA-Z\\-_][0-9a-zA-Z\\-_]*$', message="Code can only contain the letters a-z, A-Z, digits, minus and underscores, and can't start with a digit")], max_length=128)),
                ('type', models.CharField(verbose_name='Type', choices=[('text', 'Text'), ('integer', 'Integer'), ('boolean', 'True / False'), ('float', 'Float'), ('richtext', 'Rich Text'), ('date', 'Date'), ('option', 'Option'), ('entity', 'Entity'), ('file', 'File'), ('image', 'Image')], default='text', max_length=20)),
                ('required', models.BooleanField(verbose_name='Required', default=False)),
                ('option_group', models.ForeignKey(verbose_name='Option Group', blank=True, help_text='Select an option group if using type "Option"', to='catalogue.AttributeOptionGroup', null=True)),
            ],
            options={
                'verbose_name': 'Product attribute',
                'verbose_name_plural': 'Product attributes',
                'ordering': ['code'],
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='ProductAttributeValue',
            fields=[
                ('id', models.AutoField(auto_created=True, verbose_name='ID', primary_key=True, serialize=False)),
                ('value_text', models.TextField(verbose_name='Text', blank=True, null=True)),
                ('value_integer', models.IntegerField(verbose_name='Integer', blank=True, null=True)),
                ('value_boolean', models.NullBooleanField(verbose_name='Boolean')),
                ('value_float', models.FloatField(verbose_name='Float', blank=True, null=True)),
                ('value_richtext', models.TextField(verbose_name='Richtext', blank=True, null=True)),
                ('value_date', models.DateField(verbose_name='Date', blank=True, null=True)),
                ('value_file', models.FileField(null=True, upload_to='images/products/%Y/%m/', blank=True, max_length=255)),
                ('value_image', models.ImageField(null=True, upload_to='images/products/%Y/%m/', blank=True, max_length=255)),
                ('entity_object_id', models.PositiveIntegerField(editable=False, blank=True, null=True)),
                ('attribute', models.ForeignKey(verbose_name='Attribute', to='catalogue.ProductAttribute')),
                ('entity_content_type', models.ForeignKey(editable=False, blank=True, to='contenttypes.ContentType', null=True)),
            ],
            options={
                'verbose_name': 'Product attribute value',
                'verbose_name_plural': 'Product attribute values',
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.AddField(
            model_name='product',
            name='attributes',
            field=models.ManyToManyField(verbose_name='Attributes', through='catalogue.ProductAttributeValue', to='catalogue.ProductAttribute'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='productattributevalue',
            name='product',
            field=models.ForeignKey(verbose_name='Product', to='catalogue.Product'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='productattributevalue',
            name='value_option',
            field=models.ForeignKey(verbose_name='Value Option', blank=True, to='catalogue.AttributeOption', null=True),
            preserve_default=True,
        ),
        migrations.AlterUniqueTogether(
            name='productattributevalue',
            unique_together=set([('attribute', 'product')]),
        ),
        migrations.CreateModel(
            name='ProductCategory',
            fields=[
                ('id', models.AutoField(auto_created=True, verbose_name='ID', primary_key=True, serialize=False)),
                ('category', models.ForeignKey(verbose_name='Category', to='catalogue.Category')),
            ],
            options={
                'verbose_name': 'Product category',
                'verbose_name_plural': 'Product categories',
                'ordering': ['product', 'category'],
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.AddField(
            model_name='product',
            name='categories',
            field=models.ManyToManyField(verbose_name='Categories', through='catalogue.ProductCategory', to='catalogue.Category'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='productcategory',
            name='product',
            field=models.ForeignKey(verbose_name='Product', to='catalogue.Product'),
            preserve_default=True,
        ),
        migrations.AlterUniqueTogether(
            name='productcategory',
            unique_together=set([('product', 'category')]),
        ),
        migrations.CreateModel(
            name='ProductClass',
            fields=[
                ('id', models.AutoField(auto_created=True, verbose_name='ID', primary_key=True, serialize=False)),
                ('name', models.CharField(verbose_name='Name', max_length=128)),
                ('slug', oscar.models.fields.autoslugfield.AutoSlugField(editable=False, verbose_name='Slug', blank=True, max_length=128, populate_from='name', unique=True)),
                ('requires_shipping', models.BooleanField(verbose_name='Requires shipping?', default=True)),
                ('track_stock', models.BooleanField(verbose_name='Track stock levels?', default=True)),
                ('options', models.ManyToManyField(verbose_name='Options', blank=True, to='catalogue.Option')),
            ],
            options={
                'verbose_name': 'Product class',
                'verbose_name_plural': 'Product classes',
                'ordering': ['name'],
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.AddField(
            model_name='productattribute',
            name='product_class',
            field=models.ForeignKey(verbose_name='Product Type', blank=True, to='catalogue.ProductClass', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='product',
            name='product_class',
            field=models.ForeignKey(verbose_name='Product Type', on_delete=django.db.models.deletion.PROTECT, help_text='Choose what type of product this is', to='catalogue.ProductClass', null=True),
            preserve_default=True,
        ),
        migrations.CreateModel(
            name='ProductImage',
            fields=[
                ('id', models.AutoField(auto_created=True, verbose_name='ID', primary_key=True, serialize=False)),
                ('original', models.ImageField(verbose_name='Original', upload_to='images/products/%Y/%m/', max_length=255)),
                ('caption', models.CharField(verbose_name='Caption', blank=True, max_length=200)),
                ('display_order', models.PositiveIntegerField(verbose_name='Display Order', help_text='An image with a display order of zero will be the primary image for a product', default=0)),
                ('date_created', models.DateTimeField(verbose_name='Date Created', auto_now_add=True)),
                ('product', models.ForeignKey(verbose_name='Product', to='catalogue.Product')),
            ],
            options={
                'verbose_name': 'Product image',
                'verbose_name_plural': 'Product images',
                'ordering': ['display_order'],
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.AlterUniqueTogether(
            name='productimage',
            unique_together=set([('product', 'display_order')]),
        ),
        migrations.CreateModel(
            name='ProductRecommendation',
            fields=[
                ('id', models.AutoField(auto_created=True, verbose_name='ID', primary_key=True, serialize=False)),
                ('ranking', models.PositiveSmallIntegerField(verbose_name='Ranking', help_text='Determines order of the products. A product with a higher value will appear before one with a lower ranking.', default=0)),
            ],
            options={
                'verbose_name': 'Product recommendation',
                'verbose_name_plural': 'Product recomendations',
                'ordering': ['primary', '-ranking'],
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.AddField(
            model_name='product',
            name='recommended_products',
            field=models.ManyToManyField(verbose_name='Recommended Products', through='catalogue.ProductRecommendation', blank=True, to='catalogue.Product'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='productrecommendation',
            name='primary',
            field=models.ForeignKey(verbose_name='Primary Product', to='catalogue.Product'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='productrecommendation',
            name='recommendation',
            field=models.ForeignKey(verbose_name='Recommended Product', to='catalogue.Product'),
            preserve_default=True,
        ),
        migrations.AlterUniqueTogether(
            name='productrecommendation',
            unique_together=set([('primary', 'recommendation')]),
        ),
    ]
