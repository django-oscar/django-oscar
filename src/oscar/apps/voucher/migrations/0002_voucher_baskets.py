# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('basket', '0006_move_basket_vouchers'),
        ('voucher', '0001_initial'),
    ]

    state_operations = [
        migrations.AddField(
            model_name='voucher',
            name='baskets',
            field=models.ManyToManyField(related_name='vouchers', verbose_name='Baskets', to='basket.Basket', blank=True),
        ),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(state_operations=state_operations)
    ]
