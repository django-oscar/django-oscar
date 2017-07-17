# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('promotions', '0002_upgrade_django1-8'),
    ]

    operations = [
        migrations.DeleteModel(
            name='AutomaticProductList',
        ),
        migrations.RemoveField(
            model_name='handpickedproductlist',
            name='products',
        ),
        migrations.RemoveField(
            model_name='keywordpromotion',
            name='content_type',
        ),
        migrations.RemoveField(
            model_name='multiimage',
            name='images',
        ),
        migrations.AlterUniqueTogether(
            name='orderedproduct',
            unique_together=set([]),
        ),
        migrations.RemoveField(
            model_name='orderedproduct',
            name='list',
        ),
        migrations.RemoveField(
            model_name='orderedproduct',
            name='product',
        ),
        migrations.RemoveField(
            model_name='orderedproductlist',
            name='handpickedproductlist_ptr',
        ),
        migrations.RemoveField(
            model_name='orderedproductlist',
            name='tabbed_block',
        ),
        migrations.RemoveField(
            model_name='pagepromotion',
            name='content_type',
        ),
        migrations.DeleteModel(
            name='RawHTML',
        ),
        migrations.RemoveField(
            model_name='singleproduct',
            name='product',
        ),
        migrations.DeleteModel(
            name='HandPickedProductList',
        ),
        migrations.DeleteModel(
            name='Image',
        ),
        migrations.DeleteModel(
            name='KeywordPromotion',
        ),
        migrations.DeleteModel(
            name='MultiImage',
        ),
        migrations.DeleteModel(
            name='OrderedProduct',
        ),
        migrations.DeleteModel(
            name='OrderedProductList',
        ),
        migrations.DeleteModel(
            name='PagePromotion',
        ),
        migrations.DeleteModel(
            name='SingleProduct',
        ),
        migrations.DeleteModel(
            name='TabbedBlock',
        ),
    ]
