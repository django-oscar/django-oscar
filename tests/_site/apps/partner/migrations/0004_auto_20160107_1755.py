# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('partner', '0003_auto_20150604_1450'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='partner',
            options={'ordering': ('name', 'code'), 'verbose_name': 'Fulfillment partner', 'verbose_name_plural': 'Fulfillment partners', 'permissions': (('dashboard_access', 'Can access dashboard'),)},
        ),
    ]
