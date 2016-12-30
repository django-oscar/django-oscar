# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('customer', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='email',
            name='email',
            field=models.EmailField(default='', max_length=254, verbose_name='email address'),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='email',
            name='user',
            field=models.ForeignKey(related_name='emails', verbose_name='User', to=settings.AUTH_USER_MODEL, null=True),
        ),
    ]
