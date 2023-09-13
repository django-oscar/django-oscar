# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import oscar.models.fields.autoslugfield
from decimal import Decimal
import oscar.models.fields
from django.utils.module_loading import import_string
from django.conf import settings

models_AutoField = import_string(settings.DEFAULT_AUTO_FIELD)



class Migration(migrations.Migration):

    dependencies = [
        ('catalogue', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Benefit',
            fields=[
                ('id', models_AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('type', models.CharField(verbose_name='Type', max_length=128, blank=True, choices=[('Percentage', "Discount is a percentage off of the product's value"), ('Absolute', "Discount is a fixed amount off of the product's value"), ('Multibuy', 'Discount is to give the cheapest product for free'), ('Fixed price', 'Get the products that meet the condition for a fixed price'), ('Shipping absolute', 'Discount is a fixed amount of the shipping cost'), ('Shipping fixed price', 'Get shipping for a fixed price'), ('Shipping percentage', 'Discount is a percentage off of the shipping cost')])),
                ('value', oscar.models.fields.PositiveDecimalField(max_digits=12, decimal_places=2, blank=True, verbose_name='Value', null=True)),
                ('max_affected_items', models.PositiveIntegerField(verbose_name='Max Affected Items', blank=True, help_text='Set this to prevent the discount consuming all items within the range that are in the basket.', null=True)),
                ('proxy_class', oscar.models.fields.NullCharField(unique=True, verbose_name='Custom class', default=None, max_length=255)),
            ],
            options={
                'verbose_name_plural': 'Benefits',
                'verbose_name': 'Benefit',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Condition',
            fields=[
                ('id', models_AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('type', models.CharField(verbose_name='Type', max_length=128, blank=True, choices=[('Count', 'Depends on number of items in basket that are in condition range'), ('Value', 'Depends on value of items in basket that are in condition range'), ('Coverage', 'Needs to contain a set number of DISTINCT items from the condition range')])),
                ('value', oscar.models.fields.PositiveDecimalField(max_digits=12, decimal_places=2, blank=True, verbose_name='Value', null=True)),
                ('proxy_class', oscar.models.fields.NullCharField(unique=True, verbose_name='Custom class', default=None, max_length=255)),
            ],
            options={
                'verbose_name_plural': 'Conditions',
                'verbose_name': 'Condition',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='ConditionalOffer',
            fields=[
                ('id', models_AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(verbose_name='Name', unique=True, max_length=128, help_text="This is displayed within the customer's basket")),
                ('slug', oscar.models.fields.autoslugfield.AutoSlugField(populate_from='name', unique=True, verbose_name='Slug', max_length=128, editable=False, blank=True)),
                ('description', models.TextField(verbose_name='Description', help_text='This is displayed on the offer browsing page', blank=True)),
                ('offer_type', models.CharField(default='Site', max_length=128, verbose_name='Type', choices=[('Site', 'Site offer - available to all users'), ('Voucher', 'Voucher offer - only available after entering the appropriate voucher code'), ('User', 'User offer - available to certain types of user'), ('Session', 'Session offer - temporary offer, available for a user for the duration of their session')])),
                ('status', models.CharField(default='Open', max_length=64, verbose_name='Status')),
                ('priority', models.IntegerField(default=0, verbose_name='Priority', help_text='The highest priority offers are applied first')),
                ('start_datetime', models.DateTimeField(blank=True, verbose_name='Start date', null=True)),
                ('end_datetime', models.DateTimeField(verbose_name='End date', blank=True, help_text="Offers are active until the end of the 'end date'", null=True)),
                ('max_global_applications', models.PositiveIntegerField(verbose_name='Max global applications', blank=True, help_text='The number of times this offer can be used before it is unavailable', null=True)),
                ('max_user_applications', models.PositiveIntegerField(verbose_name='Max user applications', blank=True, help_text='The number of times a single user can use this offer', null=True)),
                ('max_basket_applications', models.PositiveIntegerField(verbose_name='Max basket applications', blank=True, help_text='The number of times this offer can be applied to a basket (and order)', null=True)),
                ('max_discount', models.DecimalField(verbose_name='Max discount', max_digits=12, decimal_places=2, null=True, help_text='When an offer has given more discount to orders than this threshold, then the offer becomes unavailable', blank=True)),
                ('total_discount', models.DecimalField(default=Decimal('0.00'), max_digits=12, decimal_places=2, verbose_name='Total Discount')),
                ('num_applications', models.PositiveIntegerField(default=0, verbose_name='Number of applications')),
                ('num_orders', models.PositiveIntegerField(default=0, verbose_name='Number of Orders')),
                ('redirect_url', oscar.models.fields.ExtendedURLField(verbose_name='URL redirect (optional)', blank=True)),
                ('date_created', models.DateTimeField(auto_now_add=True, verbose_name='Date Created')),
                ('benefit', models.ForeignKey(verbose_name='Benefit', to='offer.Benefit', on_delete=models.CASCADE)),
                ('condition', models.ForeignKey(verbose_name='Condition', to='offer.Condition', on_delete=models.CASCADE)),
            ],
            options={
                'ordering': ['-priority'],
                'verbose_name_plural': 'Conditional offers',
                'verbose_name': 'Conditional offer',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Range',
            fields=[
                ('id', models_AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(unique=True, max_length=128, verbose_name='Name')),
                ('slug', oscar.models.fields.autoslugfield.AutoSlugField(populate_from='name', unique=True, verbose_name='Slug', max_length=128, editable=False, blank=True)),
                ('description', models.TextField(verbose_name="Description", blank=True)),
                ('is_public', models.BooleanField(default=False, verbose_name='Is public?', help_text='Public ranges have a customer-facing page')),
                ('includes_all_products', models.BooleanField(default=False, verbose_name='Includes all products?')),
                ('proxy_class', oscar.models.fields.NullCharField(unique=True, verbose_name='Custom class', default=None, max_length=255)),
                ('date_created', models.DateTimeField(auto_now_add=True, verbose_name='Date Created')),
                ('classes', models.ManyToManyField(related_name='classes', verbose_name='Product Types', to='catalogue.ProductClass', blank=True)),
                ('excluded_products', models.ManyToManyField(related_name='excludes', verbose_name='Excluded Products', to='catalogue.Product', blank=True)),
                ('included_categories', models.ManyToManyField(related_name='includes', verbose_name='Included Categories', to='catalogue.Category', blank=True)),
            ],
            options={
                'verbose_name_plural': 'Ranges',
                'verbose_name': 'Range',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='RangeProduct',
            fields=[
                ('id', models_AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('display_order', models.IntegerField(default=0)),
                ('product', models.ForeignKey(to='catalogue.Product', on_delete=models.CASCADE)),
                ('range', models.ForeignKey(to='offer.Range', on_delete=models.CASCADE)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='RangeProductFileUpload',
            fields=[
                ('id', models_AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('filepath', models.CharField(max_length=255, verbose_name='File Path')),
                ('size', models.PositiveIntegerField(verbose_name='Size')),
                ('date_uploaded', models.DateTimeField(auto_now_add=True, verbose_name='Date Uploaded')),
                ('status', models.CharField(default='Pending', max_length=32, verbose_name='Status', choices=[('Pending', 'Pending'), ('Failed', 'Failed'), ('Processed', 'Processed')])),
                ('error_message', models.CharField(max_length=255, verbose_name='Error Message', blank=True)),
                ('date_processed', models.DateTimeField(verbose_name='Date Processed', null=True)),
                ('num_new_skus', models.PositiveIntegerField(verbose_name='Number of New SKUs', null=True)),
                ('num_unknown_skus', models.PositiveIntegerField(verbose_name='Number of Unknown SKUs', null=True)),
                ('num_duplicate_skus', models.PositiveIntegerField(verbose_name='Number of Duplicate SKUs', null=True)),
                ('range', models.ForeignKey(verbose_name='Range', related_name='file_uploads', to='offer.Range', on_delete=models.CASCADE)),
                ('uploaded_by', models.ForeignKey(verbose_name='Uploaded By', to=settings.AUTH_USER_MODEL, on_delete=models.CASCADE)),
            ],
            options={
                'ordering': ('-date_uploaded',),
                'verbose_name_plural': 'Range Product Uploaded Files',
                'verbose_name': 'Range Product Uploaded File',
            },
            bases=(models.Model,),
        ),
        migrations.AlterUniqueTogether(
            name='rangeproduct',
            unique_together=set([('range', 'product')]),
        ),
        migrations.AddField(
            model_name='range',
            name='included_products',
            field=models.ManyToManyField(related_name='includes', verbose_name='Included Products', to='catalogue.Product', through='offer.RangeProduct', blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='condition',
            name='range',
            field=models.ForeignKey(null=True, verbose_name='Range', to='offer.Range', blank=True, on_delete=models.CASCADE),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='benefit',
            name='range',
            field=models.ForeignKey(null=True, verbose_name='Range', to='offer.Range', blank=True, on_delete=models.CASCADE),
            preserve_default=True,
        ),
        migrations.CreateModel(
            name='AbsoluteDiscountBenefit',
            fields=[
            ],
            options={
                'verbose_name_plural': 'Absolute discount benefits',
                'verbose_name': 'Absolute discount benefit',
                'proxy': True,
            },
            bases=('offer.benefit',),
        ),
        migrations.CreateModel(
            name='CountCondition',
            fields=[
            ],
            options={
                'verbose_name_plural': 'Count conditions',
                'verbose_name': 'Count condition',
                'proxy': True,
            },
            bases=('offer.condition',),
        ),
        migrations.CreateModel(
            name='CoverageCondition',
            fields=[
            ],
            options={
                'verbose_name_plural': 'Coverage Conditions',
                'verbose_name': 'Coverage Condition',
                'proxy': True,
            },
            bases=('offer.condition',),
        ),
        migrations.CreateModel(
            name='FixedPriceBenefit',
            fields=[
            ],
            options={
                'verbose_name_plural': 'Fixed price benefits',
                'verbose_name': 'Fixed price benefit',
                'proxy': True,
            },
            bases=('offer.benefit',),
        ),
        migrations.CreateModel(
            name='MultibuyDiscountBenefit',
            fields=[
            ],
            options={
                'verbose_name_plural': 'Multibuy discount benefits',
                'verbose_name': 'Multibuy discount benefit',
                'proxy': True,
            },
            bases=('offer.benefit',),
        ),
        migrations.CreateModel(
            name='PercentageDiscountBenefit',
            fields=[
            ],
            options={
                'verbose_name_plural': 'Percentage discount benefits',
                'verbose_name': 'Percentage discount benefit',
                'proxy': True,
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
                'verbose_name_plural': 'Shipping absolute discount benefits',
                'verbose_name': 'Shipping absolute discount benefit',
                'proxy': True,
            },
            bases=('offer.shippingbenefit',),
        ),
        migrations.CreateModel(
            name='ShippingFixedPriceBenefit',
            fields=[
            ],
            options={
                'verbose_name_plural': 'Fixed price shipping benefits',
                'verbose_name': 'Fixed price shipping benefit',
                'proxy': True,
            },
            bases=('offer.shippingbenefit',),
        ),
        migrations.CreateModel(
            name='ShippingPercentageDiscountBenefit',
            fields=[
            ],
            options={
                'verbose_name_plural': 'Shipping percentage discount benefits',
                'verbose_name': 'Shipping percentage discount benefit',
                'proxy': True,
            },
            bases=('offer.shippingbenefit',),
        ),
        migrations.CreateModel(
            name='ValueCondition',
            fields=[
            ],
            options={
                'verbose_name_plural': 'Value conditions',
                'verbose_name': 'Value condition',
                'proxy': True,
            },
            bases=('offer.condition',),
        ),
    ]
