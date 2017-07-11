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
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255, verbose_name='Title')),
                ('description', models.TextField(verbose_name='Description', blank=True)),
                ('link_url', oscar.models.fields.ExtendedURLField(verbose_name='Link URL', blank=True)),
                ('link_text', models.CharField(max_length=255, verbose_name='Link text', blank=True)),
                ('date_created', models.DateTimeField(auto_now_add=True)),
                ('method', models.CharField(max_length=128, verbose_name='Method', choices=[('Bestselling', 'Bestselling products'), ('RecentlyAdded', 'Recently added products')])),
                ('num_products', models.PositiveSmallIntegerField(default=4, verbose_name='Number of Products')),
            ],
            options={
                'verbose_name_plural': 'Automatic product lists',
                'verbose_name': 'Automatic product list',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='HandPickedProductList',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255, verbose_name='Title')),
                ('description', models.TextField(verbose_name='Description', blank=True)),
                ('link_url', oscar.models.fields.ExtendedURLField(verbose_name='Link URL', blank=True)),
                ('link_text', models.CharField(max_length=255, verbose_name='Link text', blank=True)),
                ('date_created', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'verbose_name_plural': 'Hand Picked Product Lists',
                'verbose_name': 'Hand Picked Product List',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Image',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=128, verbose_name='Name')),
                ('link_url', oscar.models.fields.ExtendedURLField(verbose_name='Link URL', help_text='This is where this promotion links to', blank=True)),
                ('image', models.ImageField(upload_to='images/promotions/', max_length=255, verbose_name='Image')),
                ('date_created', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'verbose_name_plural': 'Image',
                'verbose_name': 'Image',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='KeywordPromotion',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('object_id', models.PositiveIntegerField()),
                ('position', models.CharField(verbose_name='Position', max_length=100, help_text='Position on page')),
                ('display_order', models.PositiveIntegerField(default=0, verbose_name='Display Order')),
                ('clicks', models.PositiveIntegerField(default=0, verbose_name='Clicks')),
                ('date_created', models.DateTimeField(auto_now_add=True, verbose_name='Date Created')),
                ('keyword', models.CharField(max_length=200, verbose_name='Keyword')),
                ('filter', models.CharField(max_length=200, verbose_name='Filter', blank=True)),
                ('content_type', models.ForeignKey(to='contenttypes.ContentType', on_delete=models.CASCADE)),
            ],
            options={
                'ordering': ['-clicks'],
                'verbose_name_plural': 'Keyword Promotions',
                'verbose_name': 'Keyword Promotion',
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='MultiImage',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=128, verbose_name='Name')),
                ('date_created', models.DateTimeField(auto_now_add=True)),
                ('images', models.ManyToManyField(blank=True, help_text='Choose the Image content blocks that this block will use. (You may need to create some first).', to='promotions.Image', null=True)),
            ],
            options={
                'verbose_name_plural': 'Multi Images',
                'verbose_name': 'Multi Image',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='OrderedProduct',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('display_order', models.PositiveIntegerField(default=0, verbose_name='Display Order')),
            ],
            options={
                'ordering': ('display_order',),
                'verbose_name_plural': 'Ordered product',
                'verbose_name': 'Ordered product',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='OrderedProductList',
            fields=[
                ('handpickedproductlist_ptr', models.OneToOneField(parent_link=True,
                                                                   serialize=False,
                                                                   auto_created=True,
                                                                   primary_key=True,
                                                                   to='promotions.HandPickedProductList',
                                                                   on_delete=models.CASCADE)),
                ('display_order', models.PositiveIntegerField(default=0, verbose_name='Display Order')),
            ],
            options={
                'ordering': ('display_order',),
                'verbose_name_plural': 'Ordered Product Lists',
                'verbose_name': 'Ordered Product List',
            },
            bases=('promotions.handpickedproductlist',),
        ),
        migrations.CreateModel(
            name='PagePromotion',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('object_id', models.PositiveIntegerField()),
                ('position', models.CharField(verbose_name='Position', max_length=100, help_text='Position on page')),
                ('display_order', models.PositiveIntegerField(default=0, verbose_name='Display Order')),
                ('clicks', models.PositiveIntegerField(default=0, verbose_name='Clicks')),
                ('date_created', models.DateTimeField(auto_now_add=True, verbose_name='Date Created')),
                ('page_url', oscar.models.fields.ExtendedURLField(max_length=128, db_index=True, verbose_name='Page URL')),
                ('content_type', models.ForeignKey(to='contenttypes.ContentType', on_delete=models.CASCADE)),
            ],
            options={
                'ordering': ['-clicks'],
                'verbose_name_plural': 'Page Promotions',
                'verbose_name': 'Page Promotion',
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='RawHTML',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=128, verbose_name='Name')),
                ('display_type', models.CharField(verbose_name='Display type', max_length=128, help_text='This can be used to have different types of HTML blocks (eg different widths)', blank=True)),
                ('body', models.TextField(verbose_name='HTML')),
                ('date_created', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'verbose_name_plural': 'Raw HTML',
                'verbose_name': 'Raw HTML',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='SingleProduct',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=128, verbose_name='Name')),
                ('description', models.TextField(verbose_name='Description', blank=True)),
                ('date_created', models.DateTimeField(auto_now_add=True)),
                ('product', models.ForeignKey(to='catalogue.Product', on_delete=models.CASCADE)),
            ],
            options={
                'verbose_name_plural': 'Single product',
                'verbose_name': 'Single product',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='TabbedBlock',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255, verbose_name='Title')),
                ('date_created', models.DateTimeField(auto_now_add=True, verbose_name='Date Created')),
            ],
            options={
                'verbose_name_plural': 'Tabbed Blocks',
                'verbose_name': 'Tabbed Block',
            },
            bases=(models.Model,),
        ),
        migrations.AddField(
            model_name='orderedproductlist',
            name='tabbed_block',
            field=models.ForeignKey(verbose_name='Tabbed Block', related_name='tabs', to='promotions.TabbedBlock', on_delete=models.CASCADE),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='orderedproduct',
            name='list',
            field=models.ForeignKey(verbose_name='List', to='promotions.HandPickedProductList', on_delete=models.CASCADE),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='orderedproduct',
            name='product',
            field=models.ForeignKey(verbose_name='Product', to='catalogue.Product', on_delete=models.CASCADE),
            preserve_default=True,
        ),
        migrations.AlterUniqueTogether(
            name='orderedproduct',
            unique_together=set([('list', 'product')]),
        ),
        migrations.AddField(
            model_name='handpickedproductlist',
            name='products',
            field=models.ManyToManyField(through='promotions.OrderedProduct', blank=True, verbose_name='Products', to='catalogue.Product', null=True),
            preserve_default=True,
        ),
    ]
