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
                ('id', models.AutoField(auto_created=True, verbose_name='ID', primary_key=True, serialize=False)),
                ('status', models.CharField(verbose_name='Status', choices=[('Open', 'Open - currently active'), ('Merged', 'Merged - superceded by another basket'), ('Saved', 'Saved - for items to be purchased later'), ('Frozen', 'Frozen - the basket cannot be modified'), ('Submitted', 'Submitted - has been ordered at the checkout')], default='Open', max_length=128)),
                ('date_created', models.DateTimeField(verbose_name='Date created', auto_now_add=True)),
                ('date_merged', models.DateTimeField(verbose_name='Date merged', blank=True, null=True)),
                ('date_submitted', models.DateTimeField(verbose_name='Date submitted', blank=True, null=True)),
                ('owner', models.ForeignKey(verbose_name='Owner', to=settings.AUTH_USER_MODEL, null=True)),
            ],
            options={
                'verbose_name': 'Basket',
                'verbose_name_plural': 'Baskets',
                'abstract': False,
            },
            bases=(models.Model,),
        ),
    ]
