# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import oscar.models.fields.autoslugfield
from decimal import Decimal
import oscar.models.fields
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
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('type', models.CharField(blank=True, max_length=128, verbose_name='Type', choices=[(b'Percentage', "Discount is a percentage off of the product's value"), (b'Absolute', "Discount is a fixed amount off of the product's value"), (b'Multibuy', 'Discount is to give the cheapest product for free'), (b'Fixed price', 'Get the products that meet the condition for a fixed price'), (b'Shipping absolute', 'Discount is a fixed amount of the shipping cost'), (b'Shipping fixed price', 'Get shipping for a fixed price'), (b'Shipping percentage', 'Discount is a percentage off of the shipping cost')])),
                ('value', oscar.models.fields.PositiveDecimalField(null=True, verbose_name='Value', max_digits=12, decimal_places=2, blank=True)),
                ('max_affected_items', models.PositiveIntegerField(help_text='Set this to prevent the discount consuming all items within the range that are in the basket.', null=True, verbose_name='Max Affected Items', blank=True)),
                ('proxy_class', oscar.models.fields.NullCharField(default=None, max_length=255, unique=True, verbose_name='Custom class')),
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
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('type', models.CharField(blank=True, max_length=128, verbose_name='Type', choices=[(b'Count', 'Depends on number of items in basket that are in condition range'), (b'Value', 'Depends on value of items in basket that are in condition range'), (b'Coverage', 'Needs to contain a set number of DISTINCT items from the condition range')])),
                ('value', oscar.models.fields.PositiveDecimalField(null=True, verbose_name='Value', max_digits=12, decimal_places=2, blank=True)),
                ('proxy_class', oscar.models.fields.NullCharField(default=None, max_length=255, unique=True, verbose_name='Custom class')),
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
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(help_text="This is displayed within the customer's basket", unique=True, max_length=128, verbose_name='Name')),
                ('slug', oscar.models.fields.autoslugfield.AutoSlugField(populate_from=b'name', editable=False, max_length=128, blank=True, unique=True, verbose_name='Slug')),
                ('description', models.TextField(help_text='This is displayed on the offer browsing page', verbose_name='Description', blank=True)),
                ('offer_type', models.CharField(default=b'Site', max_length=128, verbose_name='Type', choices=[(b'Site', 'Site offer - available to all users'), (b'Voucher', 'Voucher offer - only available after entering the appropriate voucher code'), (b'User', 'User offer - available to certain types of user'), (b'Session', 'Session offer - temporary offer, available for a user for the duration of their session')])),
                ('status', models.CharField(default=b'Open', max_length=64, verbose_name='Status')),
                ('priority', models.IntegerField(default=0, help_text='The highest priority offers are applied first', verbose_name='Priority')),
                ('start_datetime', models.DateTimeField(null=True, verbose_name='Start date', blank=True)),
                ('end_datetime', models.DateTimeField(help_text="Offers are active until the end of the 'end date'", null=True, verbose_name='End date', blank=True)),
                ('max_global_applications', models.PositiveIntegerField(help_text='The number of times this offer can be used before it is unavailable', null=True, verbose_name='Max global applications', blank=True)),
                ('max_user_applications', models.PositiveIntegerField(help_text='The number of times a single user can use this offer', null=True, verbose_name='Max user applications', blank=True)),
                ('max_basket_applications', models.PositiveIntegerField(help_text='The number of times this offer can be applied to a basket (and order)', null=True, verbose_name='Max basket applications', blank=True)),
                ('max_discount', models.DecimalField(decimal_places=2, max_digits=12, blank=True, help_text='When an offer has given more discount to orders than this threshold, then the offer becomes unavailable', null=True, verbose_name='Max discount')),
                ('total_discount', models.DecimalField(default=Decimal('0.00'), verbose_name='Total Discount', max_digits=12, decimal_places=2)),
                ('num_applications', models.PositiveIntegerField(default=0, verbose_name='Number of applications')),
                ('num_orders', models.PositiveIntegerField(default=0, verbose_name='Number of Orders')),
                ('redirect_url', oscar.models.fields.ExtendedURLField(verbose_name='URL redirect (optional)', blank=True)),
                ('date_created', models.DateTimeField(auto_now_add=True, verbose_name='Date Created')),
                ('benefit', models.ForeignKey(verbose_name='Benefit', to='offer.Benefit')),
                ('condition', models.ForeignKey(verbose_name='Condition', to='offer.Condition')),
            ],
            options={
                'ordering': [b'-priority'],
                'verbose_name': 'Conditional offer',
                'verbose_name_plural': 'Conditional offers',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Range',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(unique=True, max_length=128, verbose_name='Name')),
                ('slug', models.SlugField(max_length=128, unique=True, null=True, verbose_name='Slug')),
                ('description', models.TextField(blank=True)),
                ('is_public', models.BooleanField(default=False, help_text='Public ranges have a customer-facing page', verbose_name='Is public?')),
                ('includes_all_products', models.BooleanField(default=False, verbose_name='Includes all products?')),
                ('proxy_class', oscar.models.fields.NullCharField(default=None, max_length=255, unique=True, verbose_name='Custom class')),
                ('date_created', models.DateTimeField(auto_now_add=True, verbose_name='Date Created')),
                ('classes', models.ManyToManyField(to='catalogue.ProductClass', verbose_name='Product Types', blank=True)),
                ('excluded_products', models.ManyToManyField(to='catalogue.Product', verbose_name='Excluded Products', blank=True)),
                ('included_categories', models.ManyToManyField(to='catalogue.Category', verbose_name='Included Categories', blank=True)),
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
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
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
            field=models.ManyToManyField(to='catalogue.Product', verbose_name='Included Products', through='offer.RangeProduct', blank=True),
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
            unique_together=set([(b'range', b'product')]),
        ),
        migrations.CreateModel(
            name='RangeProductFileUpload',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('filepath', models.CharField(max_length=255, verbose_name='File Path')),
                ('size', models.PositiveIntegerField(verbose_name='Size')),
                ('date_uploaded', models.DateTimeField(auto_now_add=True, verbose_name='Date Uploaded')),
                ('status', models.CharField(default=b'Pending', max_length=32, verbose_name='Status', choices=[(b'Pending', b'Pending'), (b'Failed', b'Failed'), (b'Processed', b'Processed')])),
                ('error_message', models.CharField(max_length=255, verbose_name='Error Message', blank=True)),
                ('date_processed', models.DateTimeField(null=True, verbose_name='Date Processed')),
                ('num_new_skus', models.PositiveIntegerField(null=True, verbose_name='Number of New SKUs')),
                ('num_unknown_skus', models.PositiveIntegerField(null=True, verbose_name='Number of Unknown SKUs')),
                ('num_duplicate_skus', models.PositiveIntegerField(null=True, verbose_name='Number of Duplicate SKUs')),
                ('range', models.ForeignKey(verbose_name='Range', to='offer.Range')),
                ('uploaded_by', models.ForeignKey(verbose_name='Uploaded By', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': (b'-date_uploaded',),
                'verbose_name': 'Range Product Uploaded File',
                'verbose_name_plural': 'Range Product Uploaded Files',
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
