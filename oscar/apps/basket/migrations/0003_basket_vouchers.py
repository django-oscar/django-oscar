# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('voucher', '0001_initial'),
        ('basket', '0002_auto_20140827_1705'),
    ]

    operations = [
        migrations.AddField(
            model_name='basket',
            name='vouchers',
            field=models.ManyToManyField(blank=True, verbose_name='Vouchers', to='voucher.Voucher', null=True),
            preserve_default=True,
        ),
    ]
