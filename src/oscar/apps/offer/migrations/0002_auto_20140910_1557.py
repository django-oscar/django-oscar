# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('offer', '0001_initial'),
    ]

    operations = [
        migrations.DeleteModel(
            name='AbsoluteDiscountBenefit',
        ),
        migrations.DeleteModel(
            name='CountCondition',
        ),
        migrations.DeleteModel(
            name='CoverageCondition',
        ),
        migrations.DeleteModel(
            name='FixedPriceBenefit',
        ),
        migrations.DeleteModel(
            name='MultibuyDiscountBenefit',
        ),
        migrations.DeleteModel(
            name='ValueCondition',
        ),
        migrations.CreateModel(
            name='NoneCondition',
            fields=[
            ],
            options={
                'verbose_name': 'No Condition',
                'proxy': True,
                'verbose_name_plural': 'No Conditions',
            },
            bases=('offer.condition',),
        ),
        migrations.AddField(
            model_name='benefit',
            name='can_apply_with_other_benefits',
            field=models.BooleanField(default=False, help_text='All benefits that have this checked can apply to the same item.', verbose_name='Can apply with other benefits'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='benefit',
            name='type',
            field=models.CharField(blank=True, max_length=128, verbose_name='Type', choices=[(b'Percentage', "Discount is a percentage off of the product's value"), (b'Shipping absolute', 'Discount is a fixed amount of the shipping cost'), (b'Shipping fixed price', 'Get shipping for a fixed price'), (b'Shipping percentage', 'Discount is a percentage off of the shipping cost')]),
        ),
        migrations.AlterField(
            model_name='condition',
            name='type',
            field=models.CharField(blank=True, max_length=128, verbose_name='Type', choices=[(b'None', 'Place no restriction on the basket')]),
        ),
    ]
