# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('voucher', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='voucher',
            name='created',
            field=models.DateTimeField(auto_now_add=True, verbose_name='Created', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='voucherapplication',
            name='created',
            field=models.DateTimeField(auto_now_add=True, verbose_name='Created', null=True),
            preserve_default=True,
        ),
    ]
