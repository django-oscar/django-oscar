# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('shipping', '0002_upgrade_django1-8'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='weightband',
            name='method',
        ),
        migrations.RemoveField(
            model_name='weightbased',
            name='countries',
        ),
        migrations.DeleteModel(
            name='WeightBand',
        ),
        migrations.DeleteModel(
            name='WeightBased',
        ),
    ]
