# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import oscar.models.fields
from decimal import Decimal
import oscar.models.fields.autoslugfield
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('catalogue', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Benefit',
            fields=[
                ('id', models.AutoField(auto_created=True, verbose_name='ID', primary_key=True, serialize=False)),
                ('type', models.CharField(verbose_name='Type', choices=[('Percentage', "Discount is a percentage off of the product's value"), ('Absolute', "Discount is a fixed amount off of the product's value"), ('Multibuy', 'Discount is to give the cheapest product for free'), ('Fixed price', 'Get the products that meet the condition for a fixed price'), ('Shipping absolute', 'Discount is a fixed amount of the shipping cost'), ('Shipping fixed price', 'Get shipping for a fixed price'), ('Shipping percentage', 'Discount is a percentage off of the shipping cost')], blank=True, max_length=128)),
                ('value', oscar.models.fields.PositiveDecimalField(verbose_name='Value', max_digits=12, decimal_places=2, blank=True, null=True)),
                ('max_affected_items', models.PositiveIntegerField(verbose_name='Max Affected Items', blank=True, help_text='Set this to prevent the discount consuming all items within the range that are in the basket.', null=True)),
                ('proxy_class', oscar.models.fields.NullCharField(verbose_name='Custom class', default=None, max_length=255, unique=True)),
            ],
            options={
                'verbose_name': 'Benefit',
                'verbose_name_plural': 'Benefits',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Condition',
            fields=[
                ('id', models.AutoField(auto_created=True, verbose_name='ID', primary_key=True, serialize=False)),
                ('type', models.CharField(verbose_name='Type', choices=[('Count', 'Depends on number of items in basket that are in condition range'), ('Value', 'Depends on value of items in basket that are in condition range'), ('Coverage', 'Needs to contain a set number of DISTINCT items from the condition range')], blank=True, max_length=128)),
                ('value', oscar.models.fields.PositiveDecimalField(verbose_name='Value', max_digits=12, decimal_places=2, blank=True, null=True)),
                ('proxy_class', oscar.models.fields.NullCharField(verbose_name='Custom class', default=None, max_length=255, unique=True)),
            ],
            options={
                'verbose_name': 'Condition',
                'verbose_name_plural': 'Conditions',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='ConditionalOffer',
            fields=[
                ('id', models.AutoField(auto_created=True, verbose_name='ID', primary_key=True, serialize=False)),
                ('name', models.CharField(verbose_name='Name', unique=True, help_text="This is displayed within the customer's basket", max_length=128)),
                ('slug', oscar.models.fields.autoslugfield.AutoSlugField(editable=False, verbose_name='Slug', blank=True, max_length=128, populate_from='name', unique=True)),
                ('description', models.TextField(verbose_name='Description', blank=True, help_text='This is displayed on the offer browsing page')),
                ('offer_type', models.CharField(verbose_name='Type', choices=[('Site', 'Site offer - available to all users'), ('Voucher', 'Voucher offer - only available after entering the appropriate voucher code'), ('User', 'User offer - available to certain types of user'), ('Session', 'Session offer - temporary offer, available for a user for the duration of their session')], default='Site', max_length=128)),
                ('status', models.CharField(verbose_name='Status', default='Open', max_length=64)),
                ('priority', models.IntegerField(verbose_name='Priority', help_text='The highest priority offers are applied first', default=0)),
                ('start_datetime', models.DateTimeField(verbose_name='Start date', blank=True, null=True)),
                ('end_datetime', models.DateTimeField(verbose_name='End date', blank=True, help_text="Offers are active until the end of the 'end date'", null=True)),
                ('max_global_applications', models.PositiveIntegerField(verbose_name='Max global applications', blank=True, help_text='The number of times this offer can be used before it is unavailable', null=True)),
                ('max_user_applications', models.PositiveIntegerField(verbose_name='Max user applications', blank=True, help_text='The number of times a single user can use this offer', null=True)),
                ('max_basket_applications', models.PositiveIntegerField(verbose_name='Max basket applications', blank=True, help_text='The number of times this offer can be applied to a basket (and order)', null=True)),
                ('max_discount', models.DecimalField(verbose_name='Max discount', decimal_places=2, blank=True, max_digits=12, help_text='When an offer has given more discount to orders than this threshold, then the offer becomes unavailable', null=True)),
                ('total_discount', models.DecimalField(verbose_name='Total Discount', max_digits=12, decimal_places=2, default=Decimal('0.00'))),
                ('num_applications', models.PositiveIntegerField(verbose_name='Number of applications', default=0)),
                ('num_orders', models.PositiveIntegerField(verbose_name='Number of Orders', default=0)),
                ('redirect_url', oscar.models.fields.ExtendedURLField(verbose_name='URL redirect (optional)', blank=True)),
                ('date_created', models.DateTimeField(verbose_name='Date Created', auto_now_add=True)),
                ('benefit', models.ForeignKey(verbose_name='Benefit', to='offer.Benefit')),
                ('condition', models.ForeignKey(verbose_name='Condition', to='offer.Condition')),
            ],
            options={
                'verbose_name': 'Conditional offer',
                'verbose_name_plural': 'Conditional offers',
                'ordering': ['-priority'],
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Range',
            fields=[
                ('id', models.AutoField(auto_created=True, verbose_name='ID', primary_key=True, serialize=False)),
                ('name', models.CharField(verbose_name='Name', unique=True, max_length=128)),
                ('slug', oscar.models.fields.autoslugfield.AutoSlugField(editable=False, verbose_name='Slug', blank=True, max_length=128, populate_from='name', unique=True)),
                ('description', models.TextField(blank=True)),
                ('is_public', models.BooleanField(verbose_name='Is public?', help_text='Public ranges have a customer-facing page', default=False)),
                ('includes_all_products', models.BooleanField(verbose_name='Includes all products?', default=False)),
                ('proxy_class', oscar.models.fields.NullCharField(verbose_name='Custom class', default=None, max_length=255, unique=True)),
                ('date_created', models.DateTimeField(verbose_name='Date Created', auto_now_add=True)),
                ('classes', models.ManyToManyField(verbose_name='Product Types', blank=True, to='catalogue.ProductClass')),
                ('excluded_products', models.ManyToManyField(verbose_name='Excluded Products', blank=True, to='catalogue.Product')),
                ('included_categories', models.ManyToManyField(verbose_name='Included Categories', blank=True, to='catalogue.Category')),
            ],
            options={
                'verbose_name': 'Range',
                'verbose_name_plural': 'Ranges',
            },
            bases=(models.Model,),
        ),
        migrations.AddField(
            model_name='condition',
            name='range',
            field=models.ForeignKey(verbose_name='Range', blank=True, to='offer.Range', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='benefit',
            name='range',
            field=models.ForeignKey(verbose_name='Range', blank=True, to='offer.Range', null=True),
            preserve_default=True,
        ),
        migrations.CreateModel(
            name='RangeProduct',
            fields=[
                ('id', models.AutoField(auto_created=True, verbose_name='ID', primary_key=True, serialize=False)),
                ('display_order', models.IntegerField(default=0)),
                ('product', models.ForeignKey(to='catalogue.Product')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.AddField(
            model_name='range',
            name='included_products',
            field=models.ManyToManyField(verbose_name='Included Products', through='offer.RangeProduct', blank=True, to='catalogue.Product'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='rangeproduct',
            name='range',
            field=models.ForeignKey(to='offer.Range'),
            preserve_default=True,
        ),
        migrations.AlterUniqueTogether(
            name='rangeproduct',
            unique_together=set([('range', 'product')]),
        ),
        migrations.CreateModel(
            name='RangeProductFileUpload',
            fields=[
                ('id', models.AutoField(auto_created=True, verbose_name='ID', primary_key=True, serialize=False)),
                ('filepath', models.CharField(verbose_name='File Path', max_length=255)),
                ('size', models.PositiveIntegerField(verbose_name='Size')),
                ('date_uploaded', models.DateTimeField(verbose_name='Date Uploaded', auto_now_add=True)),
                ('status', models.CharField(verbose_name='Status', choices=[('Pending', 'Pending'), ('Failed', 'Failed'), ('Processed', 'Processed')], default='Pending', max_length=32)),
                ('error_message', models.CharField(verbose_name='Error Message', blank=True, max_length=255)),
                ('date_processed', models.DateTimeField(verbose_name='Date Processed', null=True)),
                ('num_new_skus', models.PositiveIntegerField(verbose_name='Number of New SKUs', null=True)),
                ('num_unknown_skus', models.PositiveIntegerField(verbose_name='Number of Unknown SKUs', null=True)),
                ('num_duplicate_skus', models.PositiveIntegerField(verbose_name='Number of Duplicate SKUs', null=True)),
                ('range', models.ForeignKey(verbose_name='Range', to='offer.Range')),
                ('uploaded_by', models.ForeignKey(verbose_name='Uploaded By', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Range Product Uploaded File',
                'verbose_name_plural': 'Range Product Uploaded Files',
                'ordering': ('-date_uploaded',),
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='AbsoluteDiscountBenefit',
            fields=[
            ],
            options={
                'verbose_name': 'Absolute discount benefit',
                'proxy': True,
                'verbose_name_plural': 'Absolute discount benefits',
            },
            bases=('offer.benefit',),
        ),
        migrations.CreateModel(
            name='CountCondition',
            fields=[
            ],
            options={
                'verbose_name': 'Count condition',
                'proxy': True,
                'verbose_name_plural': 'Count conditions',
            },
            bases=('offer.condition',),
        ),
        migrations.CreateModel(
            name='CoverageCondition',
            fields=[
            ],
            options={
                'verbose_name': 'Coverage Condition',
                'proxy': True,
                'verbose_name_plural': 'Coverage Conditions',
            },
            bases=('offer.condition',),
        ),
        migrations.CreateModel(
            name='FixedPriceBenefit',
            fields=[
            ],
            options={
                'verbose_name': 'Fixed price benefit',
                'proxy': True,
                'verbose_name_plural': 'Fixed price benefits',
            },
            bases=('offer.benefit',),
        ),
        migrations.CreateModel(
            name='MultibuyDiscountBenefit',
            fields=[
            ],
            options={
                'verbose_name': 'Multibuy discount benefit',
                'proxy': True,
                'verbose_name_plural': 'Multibuy discount benefits',
            },
            bases=('offer.benefit',),
        ),
        migrations.CreateModel(
            name='PercentageDiscountBenefit',
            fields=[
            ],
            options={
                'verbose_name': 'Percentage discount benefit',
                'proxy': True,
                'verbose_name_plural': 'Percentage discount benefits',
            },
            bases=('offer.benefit',),
        ),
        migrations.CreateModel(
            name='ShippingBenefit',
            fields=[
            ],
            options={
                'proxy': True,
            },
            bases=('offer.benefit',),
        ),
        migrations.CreateModel(
            name='ShippingAbsoluteDiscountBenefit',
            fields=[
            ],
            options={
                'verbose_name': 'Shipping absolute discount benefit',
                'proxy': True,
                'verbose_name_plural': 'Shipping absolute discount benefits',
            },
            bases=('offer.shippingbenefit',),
        ),
        migrations.CreateModel(
            name='ShippingFixedPriceBenefit',
            fields=[
            ],
            options={
                'verbose_name': 'Fixed price shipping benefit',
                'proxy': True,
                'verbose_name_plural': 'Fixed price shipping benefits',
            },
            bases=('offer.shippingbenefit',),
        ),
        migrations.CreateModel(
            name='ShippingPercentageDiscountBenefit',
            fields=[
            ],
            options={
                'verbose_name': 'Shipping percentage discount benefit',
                'proxy': True,
                'verbose_name_plural': 'Shipping percentage discount benefits',
            },
            bases=('offer.shippingbenefit',),
        ),
        migrations.CreateModel(
            name='ValueCondition',
            fields=[
            ],
            options={
                'verbose_name': 'Value condition',
                'proxy': True,
                'verbose_name_plural': 'Value conditions',
            },
            bases=('offer.condition',),
        ),
    ]
