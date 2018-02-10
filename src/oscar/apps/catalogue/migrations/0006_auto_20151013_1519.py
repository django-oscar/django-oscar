# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('catalogue', '0005_auto_20150604_1450'),
    ]

    operations = [
        migrations.AddField(
            model_name='product',
            name='child_images',
            field=models.ManyToManyField(related_name='children', verbose_name=b'Child images', to='catalogue.ProductImage', blank=b'True'),
        ),
    ]
