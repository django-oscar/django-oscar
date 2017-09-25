# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('shipping', '0003_auto_20170712_1402'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='orderanditemcharges',
            name='countries',
        ),
        migrations.DeleteModel(
            name='OrderAndItemCharges',
        ),
    ]
