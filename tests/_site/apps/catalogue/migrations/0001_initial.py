# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import oscar.models.fields.autoslugfield
import django.db.models.deletion
import django.core.validators
import oscar.models.fields


class Migration(migrations.Migration):

    dependencies = [
        ('contenttypes', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='AttributeOption',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('option', models.CharField(max_length=255, verbose_name='Option')),
            ],
            options={
                'verbose_name_plural': 'Attribute options',
                'verbose_name': 'Attribute option',
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='AttributeOptionGroup',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=128, verbose_name='Name')),
            ],
            options={
                'verbose_name_plural': 'Attribute option groups',
                'verbose_name': 'Attribute option group',
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Category',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('path', models.CharField(unique=True, max_length=255)),
                ('depth', models.PositiveIntegerField()),
                ('numchild', models.PositiveIntegerField(default=0)),
                ('name', models.CharField(max_length=255, db_index=True, verbose_name='Name')),
                ('description', models.TextField(verbose_name='Description', blank=True)),
                ('image', models.ImageField(upload_to='categories', verbose_name='Image', max_length=255, blank=True, null=True)),
                ('slug', models.SlugField(max_length=255, editable=False, verbose_name='Slug')),
                ('full_name', models.CharField(max_length=255, editable=False, db_index=True, verbose_name='Full Name')),
            ],
            options={
                'ordering': ['full_name'],
                'verbose_name_plural': 'Categories',
                'verbose_name': 'Category',
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Option',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=128, verbose_name='Name')),
                ('code', oscar.models.fields.autoslugfield.AutoSlugField(populate_from='name', unique=True, verbose_name='Code', max_length=128, editable=False, blank=True)),
                ('type', models.CharField(default='Required', max_length=128, verbose_name='Status', choices=[('Required', 'Required - a value for this option must be specified'), ('Optional', 'Optional - a value for this option can be omitted')])),
            ],
            options={
                'verbose_name_plural': 'Options',
                'verbose_name': 'Option',
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Product',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('structure', models.CharField(default='standalone', max_length=10, verbose_name='Product structure', choices=[('standalone', 'Stand-alone product'), ('parent', 'Parent product'), ('child', 'Child product')])),
                ('upc', oscar.models.fields.NullCharField(unique=True, verbose_name='UPC', max_length=64, help_text='Universal Product Code (UPC) is an identifier for a product which is not specific to a particular  supplier. Eg an ISBN for a book.')),
                ('title', models.CharField(max_length=255, verbose_name='Title', blank=True)),
                ('slug', models.SlugField(max_length=255, verbose_name='Slug')),
                ('description', models.TextField(verbose_name='Description', blank=True)),
                ('rating', models.FloatField(editable=False, verbose_name='Rating', null=True)),
                ('date_created', models.DateTimeField(auto_now_add=True, verbose_name='Date created')),
                ('date_updated', models.DateTimeField(auto_now=True, db_index=True, verbose_name='Date updated')),
                ('is_discountable', models.BooleanField(default=True, verbose_name='Is discountable?', help_text='This flag indicates if this product can be used in an offer or not')),
            ],
            options={
                'ordering': ['-date_created'],
                'verbose_name_plural': 'Products',
                'verbose_name': 'Product',
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='ProductAttribute',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=128, verbose_name='Name')),
                ('code', models.SlugField(max_length=128, verbose_name='Code', validators=[django.core.validators.RegexValidator(regex='^[a-zA-Z\\-_][0-9a-zA-Z\\-_]*$', message="Code can only contain the letters a-z, A-Z, digits, minus and underscores, and can't start with a digit")])),
                ('type', models.CharField(default='text', max_length=20, verbose_name='Type', choices=[('text', 'Text'), ('integer', 'Integer'), ('boolean', 'True / False'), ('float', 'Float'), ('richtext', 'Rich Text'), ('date', 'Date'), ('option', 'Option'), ('entity', 'Entity'), ('file', 'File'), ('image', 'Image')])),
                ('required', models.BooleanField(default=False, verbose_name='Required')),
                ('option_group', models.ForeignKey(null=True, verbose_name='Option Group', help_text='Select an option group if using type "Option"', to='catalogue.AttributeOptionGroup', blank=True, on_delete=models.CASCADE)),
            ],
            options={
                'ordering': ['code'],
                'verbose_name_plural': 'Product attributes',
                'verbose_name': 'Product attribute',
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='ProductAttributeValue',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('value_text', models.TextField(blank=True, verbose_name='Text', null=True)),
                ('value_integer', models.IntegerField(blank=True, verbose_name='Integer', null=True)),
                ('value_boolean', models.NullBooleanField(verbose_name='Boolean')),
                ('value_float', models.FloatField(blank=True, verbose_name='Float', null=True)),
                ('value_richtext', models.TextField(blank=True, verbose_name='Richtext', null=True)),
                ('value_date', models.DateField(blank=True, verbose_name='Date', null=True)),
                ('value_file', models.FileField(upload_to='images/products/%Y/%m/', max_length=255, blank=True, null=True)),
                ('value_image', models.ImageField(upload_to='images/products/%Y/%m/', max_length=255, blank=True, null=True)),
                ('entity_object_id', models.PositiveIntegerField(blank=True, editable=False, null=True)),
                ('attribute', models.ForeignKey(verbose_name='Attribute', to='catalogue.ProductAttribute', on_delete=models.CASCADE)),
                ('entity_content_type', models.ForeignKey(null=True, editable=False, to='contenttypes.ContentType', blank=True, on_delete=models.CASCADE)),
                ('product', models.ForeignKey(verbose_name='Product', related_name='attribute_values', to='catalogue.Product', on_delete=models.CASCADE)),
                ('value_option', models.ForeignKey(null=True, verbose_name='Value option', to='catalogue.AttributeOption', blank=True, on_delete=models.CASCADE)),
            ],
            options={
                'verbose_name_plural': 'Product attribute values',
                'verbose_name': 'Product attribute value',
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='ProductCategory',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('category', models.ForeignKey(verbose_name='Category', to='catalogue.Category', on_delete=models.CASCADE)),
                ('product', models.ForeignKey(verbose_name='Product', to='catalogue.Product', on_delete=models.CASCADE)),
            ],
            options={
                'ordering': ['product', 'category'],
                'verbose_name_plural': 'Product categories',
                'verbose_name': 'Product category',
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='ProductClass',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=128, verbose_name='Name')),
                ('slug', oscar.models.fields.autoslugfield.AutoSlugField(populate_from='name', unique=True, verbose_name='Slug', max_length=128, editable=False, blank=True)),
                ('requires_shipping', models.BooleanField(default=True, verbose_name='Requires shipping?')),
                ('track_stock', models.BooleanField(default=True, verbose_name='Track stock levels?')),
                ('options', models.ManyToManyField(verbose_name='Options', to='catalogue.Option', blank=True)),
            ],
            options={
                'ordering': ['name'],
                'verbose_name_plural': 'Product classes',
                'verbose_name': 'Product class',
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='ProductImage',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('original', models.ImageField(upload_to='images/products/%Y/%m/', max_length=255, verbose_name='Original')),
                ('caption', models.CharField(max_length=200, verbose_name='Caption', blank=True)),
                ('display_order', models.PositiveIntegerField(default=0, verbose_name='Display order', help_text='An image with a display order of zero will be the primary image for a product')),
                ('date_created', models.DateTimeField(auto_now_add=True, verbose_name='Date created')),
                ('product', models.ForeignKey(verbose_name='Product', related_name='images', to='catalogue.Product', on_delete=models.CASCADE)),
            ],
            options={
                'ordering': ['display_order'],
                'verbose_name_plural': 'Product images',
                'verbose_name': 'Product image',
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='ProductRecommendation',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('ranking', models.PositiveSmallIntegerField(default=0, verbose_name='Ranking', help_text='Determines order of the products. A product with a higher value will appear before one with a lower ranking.')),
                ('primary', models.ForeignKey(verbose_name='Primary product', related_name='primary_recommendations', to='catalogue.Product', on_delete=models.CASCADE)),
                ('recommendation', models.ForeignKey(verbose_name='Recommended product', to='catalogue.Product', on_delete=models.CASCADE)),
            ],
            options={
                'ordering': ['primary', '-ranking'],
                'verbose_name_plural': 'Product recomendations',
                'verbose_name': 'Product recommendation',
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.AlterUniqueTogether(
            name='productrecommendation',
            unique_together=set([('primary', 'recommendation')]),
        ),
        migrations.AlterUniqueTogether(
            name='productimage',
            unique_together=set([('product', 'display_order')]),
        ),
        migrations.AlterUniqueTogether(
            name='productcategory',
            unique_together=set([('product', 'category')]),
        ),
        migrations.AlterUniqueTogether(
            name='productattributevalue',
            unique_together=set([('attribute', 'product')]),
        ),
        migrations.AddField(
            model_name='productattribute',
            name='product_class',
            field=models.ForeignKey(null=True, verbose_name='Product type', related_name='attributes', to='catalogue.ProductClass', blank=True, on_delete=models.CASCADE),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='product',
            name='attributes',
            field=models.ManyToManyField(verbose_name='Attributes', help_text='A product attribute is something that this product may have, such as a size, as specified by its class', to='catalogue.ProductAttribute', through='catalogue.ProductAttributeValue'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='product',
            name='categories',
            field=models.ManyToManyField(through='catalogue.ProductCategory', verbose_name='Categories', to='catalogue.Category'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='product',
            name='parent',
            field=models.ForeignKey(null=True, verbose_name='Parent product', related_name='children', help_text="Only choose a parent product if you're creating a child product.  For example if this is a size 4 of a particular t-shirt.  Leave blank if this is a stand-alone product (i.e. there is only one version of this product).", to='catalogue.Product', blank=True, on_delete=models.CASCADE),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='product',
            name='product_class',
            field=models.ForeignKey(verbose_name='Product type', on_delete=django.db.models.deletion.PROTECT, related_name='products', help_text='Choose what type of product this is', to='catalogue.ProductClass', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='product',
            name='product_options',
            field=models.ManyToManyField(verbose_name='Product options', help_text="Options are values that can be associated with a item when it is added to a customer's basket.  This could be something like a personalised message to be printed on a T-shirt.", to='catalogue.Option', blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='product',
            name='recommended_products',
            field=models.ManyToManyField(verbose_name='Recommended products', help_text='These are products that are recommended to accompany the main product.', to='catalogue.Product', through='catalogue.ProductRecommendation', blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='attributeoption',
            name='group',
            field=models.ForeignKey(verbose_name='Group', related_name='options', to='catalogue.AttributeOptionGroup', on_delete=models.CASCADE),
            preserve_default=True,
        ),
    ]
