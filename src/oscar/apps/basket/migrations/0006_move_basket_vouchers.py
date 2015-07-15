# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('basket', '0005_auto_20150604_1450'),
    ]

    state_operations = [
        migrations.RemoveField(
            model_name='basket',
            name='vouchers'
        ),
    ]

    database_operations = [
        migrations.AlterField(
            model_name='basket',
            name='vouchers',
            field=models.ManyToManyField(to='voucher.Voucher', db_table=b'voucher_voucher_baskets', verbose_name='Vouchers', blank=True),
        ),
    ]
    
    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=database_operations,
            state_operations=state_operations)
    ]
