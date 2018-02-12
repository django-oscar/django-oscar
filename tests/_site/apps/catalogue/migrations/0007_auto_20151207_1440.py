# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('catalogue', '0006_auto_20150807_1725'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='attributeoption',
            unique_together=set([('group', 'option')]),
        ),
    ]
