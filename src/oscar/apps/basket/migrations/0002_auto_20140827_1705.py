# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('partner', '0001_initial'),
        ('catalogue', '0001_initial'),
        ('basket', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name='lineattribute',
            name='option',
            field=models.ForeignKey(verbose_name='Option', to='catalogue.Option', on_delete=models.CASCADE),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='line',
            name='basket',
            field=models.ForeignKey(verbose_name='Basket', related_name='lines', to='basket.Basket', on_delete=models.CASCADE),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='line',
            name='product',
            field=models.ForeignKey(verbose_name='Product', related_name='basket_lines', to='catalogue.Product', on_delete=models.CASCADE),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='line',
            name='stockrecord',
            field=models.ForeignKey(related_name='basket_lines', to='partner.StockRecord', on_delete=models.CASCADE),
            preserve_default=True,
        ),
        migrations.AlterUniqueTogether(
            name='line',
            unique_together=set([('basket', 'line_reference')]),
        ),
        migrations.AddField(
            model_name='basket',
            name='owner',
            field=models.ForeignKey(verbose_name='Owner', related_name='baskets', to=settings.AUTH_USER_MODEL, null=True, on_delete=models.CASCADE),
            preserve_default=True,
        ),
    ]
