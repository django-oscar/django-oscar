# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('address', '0002_auto_20150927_1547'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='useraddress',
            options={'ordering': ['-num_orders_as_shipping_address'], 'verbose_name': 'User address',
                     'verbose_name_plural': 'User addresses'},
        ),
        migrations.AlterField(
            model_name='useraddress',
            name='num_orders_as_billing_address',
            field=models.PositiveIntegerField(default=0, verbose_name='Number of Orders as Shipping Address'),
        ),
        migrations.AlterField(
            model_name='useraddress',
            name='num_orders_as_shipping_address',
            field=models.PositiveIntegerField(default=0, verbose_name='Number of Orders as Billing Address'),
        ),
    ]
