# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('wishlists', '0001_initial'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='line',
            unique_together=set([]),
        ),
        migrations.RemoveField(
            model_name='line',
            name='product',
        ),
        migrations.RemoveField(
            model_name='line',
            name='wishlist',
        ),
        migrations.RemoveField(
            model_name='wishlist',
            name='owner',
        ),
        migrations.DeleteModel(
            name='Line',
        ),
        migrations.DeleteModel(
            name='WishList',
        ),
    ]
