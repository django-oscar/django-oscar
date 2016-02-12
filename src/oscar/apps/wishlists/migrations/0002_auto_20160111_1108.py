# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('wishlists', '0001_initial'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='line',
            options={'ordering': ['pk'], 'verbose_name': 'Wish list line'},
        ),
    ]
