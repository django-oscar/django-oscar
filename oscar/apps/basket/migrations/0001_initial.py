# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Basket',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('status', models.CharField(default=b'Open', max_length=128, verbose_name='Status', choices=[(b'Open', 'Open - currently active'), (b'Merged', 'Merged - superceded by another basket'), (b'Saved', 'Saved - for items to be purchased later'), (b'Frozen', 'Frozen - the basket cannot be modified'), (b'Submitted', 'Submitted - has been ordered at the checkout')])),
                ('date_created', models.DateTimeField(auto_now_add=True, verbose_name='Date created')),
                ('date_merged', models.DateTimeField(null=True, verbose_name='Date merged', blank=True)),
                ('date_submitted', models.DateTimeField(null=True, verbose_name='Date submitted', blank=True)),
                ('owner', models.ForeignKey(verbose_name='Owner', to=settings.AUTH_USER_MODEL, null=True)),
            ],
            options={
                'abstract': False,
                'verbose_name': 'Basket',
                'verbose_name_plural': 'Baskets',
            },
            bases=(models.Model,),
        ),
    ]
