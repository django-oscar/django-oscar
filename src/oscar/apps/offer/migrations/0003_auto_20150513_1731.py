# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('offer', '0002_auto_20140910_1557'),
    ]

    operations = [
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
        migrations.AlterField(
            model_name='benefit',
            name='type',
            field=models.CharField(blank=True, max_length=128, verbose_name='Type', choices=[(b'Percentage', "Discount is a percentage off of the product's value"), (b'Fixed', "Discount is a fixed amount off of the product's value"), (b'Shipping absolute', 'Discount is a fixed amount of the shipping cost'), (b'Shipping fixed price', 'Get shipping for a fixed price'), (b'Shipping percentage', 'Discount is a percentage off of the shipping cost')]),
            preserve_default=True,
        ),
    ]
