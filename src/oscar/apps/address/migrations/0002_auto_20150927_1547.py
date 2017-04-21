# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('address', '0001_initial'),
    ]

    operations = [
        migrations.RenameField(
            model_name='useraddress',
            old_name='num_orders',
            new_name='num_orders_as_shipping_address',
        ),
        migrations.AddField(
            model_name='useraddress',
            name='num_orders_as_billing_address',
            field=models.PositiveIntegerField(default=0, verbose_name='Number of Orders as Billing Address'),
        ),
    ]
