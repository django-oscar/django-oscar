# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import oscar.models.fields.autoslugfield
import oscar.models.fields
import django.db.models.deletion
import django.core.validators


class Migration(migrations.Migration):

    dependencies = [
        ('contenttypes', '__latest__'),
    ]

    operations = [
        migrations.CreateModel(
            name='AttributeOption',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('option', models.CharField(max_length=255, verbose_name='Option')),
            ],
            options={
                'abstract': False,
                'verbose_name': 'Attribute option',
                'verbose_name_plural': 'Attribute options',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='AttributeOptionGroup',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=128, verbose_name='Name')),
            ],
            options={
                'abstract': False,
                'verbose_name': 'Attribute option group',
                'verbose_name_plural': 'Attribute option groups',
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
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('path', models.CharField(unique=True, max_length=255)),
                ('depth', models.PositiveIntegerField()),
                ('numchild', models.PositiveIntegerField(default=0)),
                ('name', models.CharField(max_length=255, verbose_name='Name', db_index=True)),
                ('description', models.TextField(verbose_name='Description', blank=True)),
                ('image', models.ImageField(max_length=255, upload_to=b'categories', null=True, verbose_name='Image', blank=True)),
                ('slug', models.SlugField(verbose_name='Slug', max_length=255, editable=False)),
                ('full_name', models.CharField(verbose_name='Full Name', max_length=255, editable=False, db_index=True)),
            ],
            options={
                'ordering': [b'full_name'],
                'abstract': False,
                'verbose_name': 'Category',
                'verbose_name_plural': 'Categories',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Option',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=128, verbose_name='Name')),
                ('code', oscar.models.fields.autoslugfield.AutoSlugField(populate_from=b'name', editable=False, max_length=128, blank=True, unique=True, verbose_name='Code')),
                ('type', models.CharField(default=b'Required', max_length=128, verbose_name='Status', choices=[(b'Required', 'Required - a value for this option must be specified'), (b'Optional', 'Optional - a value for this option can be omitted')])),
            ],
            options={
                'abstract': False,
                'verbose_name': 'Option',
                'verbose_name_plural': 'Options',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Product',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('structure', models.CharField(default=b'standalone', max_length=10, verbose_name='Product structure', choices=[(b'standalone', 'Stand-alone product'), (b'parent', 'Parent product'), (b'child', 'Child product')])),
                ('upc', oscar.models.fields.NullCharField(max_length=64, help_text='Universal Product Code (UPC) is an identifier for a product which is not specific to a particular  supplier. Eg an ISBN for a book.', unique=True, verbose_name='UPC')),
                ('title', models.CharField(max_length=255, verbose_name='Product title', blank=True)),
                ('slug', models.SlugField(max_length=255, verbose_name='Slug')),
                ('description', models.TextField(verbose_name='Description', blank=True)),
                ('rating', models.FloatField(verbose_name='Rating', null=True, editable=False)),
                ('date_created', models.DateTimeField(auto_now_add=True, verbose_name='Date created')),
                ('date_updated', models.DateTimeField(auto_now=True, verbose_name='Date updated', db_index=True)),
                ('is_discountable', models.BooleanField(default=True, help_text='This flag indicates if this product can be used in an offer or not', verbose_name='Is discountable?')),
                ('parent', models.ForeignKey(blank=True, to='catalogue.Product', help_text="Only choose a parent product if you're creating a child product.  For example if this is a size 4 of a particular t-shirt.  Leave blank if this is a stand-alone product (i.e. there is only one version of this product).", null=True, verbose_name='Parent product')),
                ('product_options', models.ManyToManyField(to='catalogue.Option', verbose_name='Product Options', blank=True)),
            ],
            options={
                'ordering': [b'-date_created'],
                'abstract': False,
                'verbose_name': 'Product',
                'verbose_name_plural': 'Products',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='ProductAttribute',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=128, verbose_name='Name')),
                ('code', models.SlugField(max_length=128, verbose_name='Code', validators=[django.core.validators.RegexValidator(regex=b'^[a-zA-Z\\-_][0-9a-zA-Z\\-_]*$', message="Code can only contain the letters a-z, A-Z, digits, minus and underscores, and can't start with a digit")])),
                ('type', models.CharField(default=b'text', max_length=20, verbose_name='Type', choices=[(b'text', 'Text'), (b'integer', 'Integer'), (b'boolean', 'True / False'), (b'float', 'Float'), (b'richtext', 'Rich Text'), (b'date', 'Date'), (b'option', 'Option'), (b'entity', 'Entity'), (b'file', 'File'), (b'image', 'Image')])),
                ('required', models.BooleanField(default=False, verbose_name='Required')),
                ('option_group', models.ForeignKey(blank=True, to='catalogue.AttributeOptionGroup', help_text='Select an option group if using type "Option"', null=True, verbose_name='Option Group')),
            ],
            options={
                'ordering': [b'code'],
                'abstract': False,
                'verbose_name': 'Product attribute',
                'verbose_name_plural': 'Product attributes',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='ProductAttributeValue',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('value_text', models.TextField(null=True, verbose_name='Text', blank=True)),
                ('value_integer', models.IntegerField(null=True, verbose_name='Integer', blank=True)),
                ('value_boolean', models.NullBooleanField(verbose_name='Boolean')),
                ('value_float', models.FloatField(null=True, verbose_name='Float', blank=True)),
                ('value_richtext', models.TextField(null=True, verbose_name='Richtext', blank=True)),
                ('value_date', models.DateField(null=True, verbose_name='Date', blank=True)),
                ('value_file', models.FileField(max_length=255, null=True, upload_to=b'images/products/%Y/%m/', blank=True)),
                ('value_image', models.ImageField(max_length=255, null=True, upload_to=b'images/products/%Y/%m/', blank=True)),
                ('entity_object_id', models.PositiveIntegerField(null=True, editable=False, blank=True)),
                ('attribute', models.ForeignKey(verbose_name='Attribute', to='catalogue.ProductAttribute')),
                ('entity_content_type', models.ForeignKey(blank=True, editable=False, to='contenttypes.ContentType', null=True)),
            ],
            options={
                'abstract': False,
                'verbose_name': 'Product attribute value',
                'verbose_name_plural': 'Product attribute values',
            },
            bases=(models.Model,),
        ),
        migrations.AddField(
            model_name='product',
            name='attributes',
            field=models.ManyToManyField(to='catalogue.ProductAttribute', verbose_name='Attributes', through='catalogue.ProductAttributeValue'),
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
            unique_together=set([(b'attribute', b'product')]),
        ),
        migrations.CreateModel(
            name='ProductCategory',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('category', models.ForeignKey(verbose_name='Category', to='catalogue.Category')),
            ],
            options={
                'ordering': [b'product', b'category'],
                'abstract': False,
                'verbose_name': 'Product category',
                'verbose_name_plural': 'Product categories',
            },
            bases=(models.Model,),
        ),
        migrations.AddField(
            model_name='product',
            name='categories',
            field=models.ManyToManyField(to='catalogue.Category', verbose_name='Categories', through='catalogue.ProductCategory'),
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
            unique_together=set([(b'product', b'category')]),
        ),
        migrations.CreateModel(
            name='ProductClass',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=128, verbose_name='Name')),
                ('slug', oscar.models.fields.autoslugfield.AutoSlugField(populate_from=b'name', editable=False, max_length=128, blank=True, unique=True, verbose_name='Slug')),
                ('requires_shipping', models.BooleanField(default=True, verbose_name='Requires shipping?')),
                ('track_stock', models.BooleanField(default=True, verbose_name='Track stock levels?')),
                ('options', models.ManyToManyField(to='catalogue.Option', verbose_name='Options', blank=True)),
            ],
            options={
                'ordering': [b'name'],
                'abstract': False,
                'verbose_name': 'Product class',
                'verbose_name_plural': 'Product classes',
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
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, verbose_name='Product Type', to='catalogue.ProductClass', help_text='Choose what type of product this is', null=True),
            preserve_default=True,
        ),
        migrations.CreateModel(
            name='ProductImage',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('original', models.ImageField(upload_to=b'images/products/%Y/%m/', max_length=255, verbose_name='Original')),
                ('caption', models.CharField(max_length=200, verbose_name='Caption', blank=True)),
                ('display_order', models.PositiveIntegerField(default=0, help_text='An image with a display order of zero will be the primary image for a product', verbose_name='Display Order')),
                ('date_created', models.DateTimeField(auto_now_add=True, verbose_name='Date Created')),
                ('product', models.ForeignKey(verbose_name='Product', to='catalogue.Product')),
            ],
            options={
                'ordering': [b'display_order'],
                'abstract': False,
                'verbose_name': 'Product image',
                'verbose_name_plural': 'Product images',
            },
            bases=(models.Model,),
        ),
        migrations.AlterUniqueTogether(
            name='productimage',
            unique_together=set([(b'product', b'display_order')]),
        ),
        migrations.CreateModel(
            name='ProductRecommendation',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('ranking', models.PositiveSmallIntegerField(default=0, help_text='Determines order of the products. A product with a higher value will appear before one with a lower ranking.', verbose_name='Ranking')),
            ],
            options={
                'ordering': [b'primary', b'-ranking'],
                'abstract': False,
                'verbose_name': 'Product recommendation',
                'verbose_name_plural': 'Product recomendations',
            },
            bases=(models.Model,),
        ),
        migrations.AddField(
            model_name='product',
            name='recommended_products',
            field=models.ManyToManyField(to='catalogue.Product', verbose_name='Recommended Products', through='catalogue.ProductRecommendation', blank=True),
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
            unique_together=set([(b'primary', b'recommendation')]),
        ),
    ]
