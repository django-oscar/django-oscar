# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import oscar.models.fields


class Migration(migrations.Migration):

    dependencies = [
        ('catalogue', '0001_initial'),
        ('contenttypes', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='AutomaticProductList',
            fields=[
                ('id', models.AutoField(auto_created=True, verbose_name='ID', primary_key=True, serialize=False)),
                ('name', models.CharField(verbose_name='Title', max_length=255)),
                ('description', models.TextField(verbose_name='Description', blank=True)),
                ('link_url', oscar.models.fields.ExtendedURLField(verbose_name='Link URL', blank=True)),
                ('link_text', models.CharField(verbose_name='Link text', blank=True, max_length=255)),
                ('date_created', models.DateTimeField(auto_now_add=True)),
                ('method', models.CharField(verbose_name='Method', choices=[('Bestselling', 'Bestselling products'), ('RecentlyAdded', 'Recently added products')], max_length=128)),
                ('num_products', models.PositiveSmallIntegerField(verbose_name='Number of Products', default=4)),
            ],
            options={
                'verbose_name': 'Automatic product list',
                'verbose_name_plural': 'Automatic product lists',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='HandPickedProductList',
            fields=[
                ('id', models.AutoField(auto_created=True, verbose_name='ID', primary_key=True, serialize=False)),
                ('name', models.CharField(verbose_name='Title', max_length=255)),
                ('description', models.TextField(verbose_name='Description', blank=True)),
                ('link_url', oscar.models.fields.ExtendedURLField(verbose_name='Link URL', blank=True)),
                ('link_text', models.CharField(verbose_name='Link text', blank=True, max_length=255)),
                ('date_created', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'verbose_name': 'Hand Picked Product List',
                'verbose_name_plural': 'Hand Picked Product Lists',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Image',
            fields=[
                ('id', models.AutoField(auto_created=True, verbose_name='ID', primary_key=True, serialize=False)),
                ('name', models.CharField(verbose_name='Name', max_length=128)),
                ('link_url', oscar.models.fields.ExtendedURLField(verbose_name='Link URL', blank=True, help_text='This is where this promotion links to')),
                ('image', models.ImageField(verbose_name='Image', upload_to='images/promotions/', max_length=255)),
                ('date_created', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'verbose_name': 'Image',
                'verbose_name_plural': 'Image',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='KeywordPromotion',
            fields=[
                ('id', models.AutoField(auto_created=True, verbose_name='ID', primary_key=True, serialize=False)),
                ('object_id', models.PositiveIntegerField()),
                ('position', models.CharField(verbose_name='Position', help_text='Position on page', max_length=100)),
                ('display_order', models.PositiveIntegerField(verbose_name='Display Order', default=0)),
                ('clicks', models.PositiveIntegerField(verbose_name='Clicks', default=0)),
                ('date_created', models.DateTimeField(verbose_name='Date Created', auto_now_add=True)),
                ('keyword', models.CharField(verbose_name='Keyword', max_length=200)),
                ('filter', models.CharField(verbose_name='Filter', blank=True, max_length=200)),
                ('content_type', models.ForeignKey(to='contenttypes.ContentType')),
            ],
            options={
                'verbose_name': 'Keyword Promotion',
                'verbose_name_plural': 'Keyword Promotions',
                'ordering': ['-clicks'],
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='MultiImage',
            fields=[
                ('id', models.AutoField(auto_created=True, verbose_name='ID', primary_key=True, serialize=False)),
                ('name', models.CharField(verbose_name='Name', max_length=128)),
                ('date_created', models.DateTimeField(auto_now_add=True)),
                ('images', models.ManyToManyField(blank=True, to='promotions.Image', null=True)),
            ],
            options={
                'verbose_name': 'Multi Image',
                'verbose_name_plural': 'Multi Images',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='OrderedProduct',
            fields=[
                ('id', models.AutoField(auto_created=True, verbose_name='ID', primary_key=True, serialize=False)),
                ('display_order', models.PositiveIntegerField(verbose_name='Display Order', default=0)),
            ],
            options={
                'verbose_name': 'Ordered product',
                'verbose_name_plural': 'Ordered product',
                'ordering': ('display_order',),
            },
            bases=(models.Model,),
        ),
        migrations.AddField(
            model_name='handpickedproductlist',
            name='products',
            field=models.ManyToManyField(verbose_name='Products', through='promotions.OrderedProduct', blank=True, to='catalogue.Product', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='orderedproduct',
            name='list',
            field=models.ForeignKey(verbose_name='List', to='promotions.HandPickedProductList'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='orderedproduct',
            name='product',
            field=models.ForeignKey(verbose_name='Product', to='catalogue.Product'),
            preserve_default=True,
        ),
        migrations.AlterUniqueTogether(
            name='orderedproduct',
            unique_together=set([('list', 'product')]),
        ),
        migrations.CreateModel(
            name='OrderedProductList',
            fields=[
                ('handpickedproductlist_ptr', models.OneToOneField(primary_key=True, serialize=False, auto_created=True, to='promotions.HandPickedProductList')),
                ('display_order', models.PositiveIntegerField(verbose_name='Display Order', default=0)),
            ],
            options={
                'verbose_name': 'Ordered Product List',
                'verbose_name_plural': 'Ordered Product Lists',
                'ordering': ('display_order',),
            },
            bases=('promotions.handpickedproductlist',),
        ),
        migrations.CreateModel(
            name='PagePromotion',
            fields=[
                ('id', models.AutoField(auto_created=True, verbose_name='ID', primary_key=True, serialize=False)),
                ('object_id', models.PositiveIntegerField()),
                ('position', models.CharField(verbose_name='Position', help_text='Position on page', max_length=100)),
                ('display_order', models.PositiveIntegerField(verbose_name='Display Order', default=0)),
                ('clicks', models.PositiveIntegerField(verbose_name='Clicks', default=0)),
                ('date_created', models.DateTimeField(verbose_name='Date Created', auto_now_add=True)),
                ('page_url', oscar.models.fields.ExtendedURLField(verbose_name='Page URL', verify_exists=True, db_index=True, max_length=128)),
                ('content_type', models.ForeignKey(to='contenttypes.ContentType')),
            ],
            options={
                'verbose_name': 'Page Promotion',
                'verbose_name_plural': 'Page Promotions',
                'ordering': ['-clicks'],
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='RawHTML',
            fields=[
                ('id', models.AutoField(auto_created=True, verbose_name='ID', primary_key=True, serialize=False)),
                ('name', models.CharField(verbose_name='Name', max_length=128)),
                ('display_type', models.CharField(verbose_name='Display type', blank=True, help_text='This can be used to have different types of HTML blocks (eg different widths)', max_length=128)),
                ('body', models.TextField(verbose_name='HTML')),
                ('date_created', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'verbose_name': 'Raw HTML',
                'verbose_name_plural': 'Raw HTML',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='SingleProduct',
            fields=[
                ('id', models.AutoField(auto_created=True, verbose_name='ID', primary_key=True, serialize=False)),
                ('name', models.CharField(verbose_name='Name', max_length=128)),
                ('description', models.TextField(verbose_name='Description', blank=True)),
                ('date_created', models.DateTimeField(auto_now_add=True)),
                ('product', models.ForeignKey(to='catalogue.Product')),
            ],
            options={
                'verbose_name': 'Single product',
                'verbose_name_plural': 'Single product',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='TabbedBlock',
            fields=[
                ('id', models.AutoField(auto_created=True, verbose_name='ID', primary_key=True, serialize=False)),
                ('name', models.CharField(verbose_name='Title', max_length=255)),
                ('date_created', models.DateTimeField(verbose_name='Date Created', auto_now_add=True)),
            ],
            options={
                'verbose_name': 'Tabbed Block',
                'verbose_name_plural': 'Tabbed Blocks',
            },
            bases=(models.Model,),
        ),
        migrations.AddField(
            model_name='orderedproductlist',
            name='tabbed_block',
            field=models.ForeignKey(verbose_name='Tabbed Block', to='promotions.TabbedBlock'),
            preserve_default=True,
        ),
    ]
