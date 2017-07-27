# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('reviews', '0002_upgrade_django1-8'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='productreview',
            unique_together=set([]),
        ),
        migrations.RemoveField(
            model_name='productreview',
            name='product',
        ),
        migrations.RemoveField(
            model_name='productreview',
            name='user',
        ),
        migrations.AlterUniqueTogether(
            name='vote',
            unique_together=set([]),
        ),
        migrations.RemoveField(
            model_name='vote',
            name='review',
        ),
        migrations.RemoveField(
            model_name='vote',
            name='user',
        ),
        migrations.DeleteModel(
            name='ProductReview',
        ),
        migrations.DeleteModel(
            name='Vote',
        ),
    ]
