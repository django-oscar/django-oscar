# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('promotions', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='handpickedproductlist',
            name='products',
            field=models.ManyToManyField(to='catalogue.Product', verbose_name='Products', through='promotions.OrderedProduct', blank=True),
        ),
        migrations.AlterField(
            model_name='multiimage',
            name='images',
            field=models.ManyToManyField(help_text='Choose the Image content blocks that this block will use. (You may need to create some first).', to='promotions.Image', blank=True),
        ),
    ]
