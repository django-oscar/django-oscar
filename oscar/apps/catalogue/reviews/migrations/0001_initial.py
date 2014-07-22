# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import oscar.core.validators
import django.db.models.deletion
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('catalogue', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='ProductReview',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('score', models.SmallIntegerField(verbose_name='Score', choices=[(0, 0), (1, 1), (2, 2), (3, 3), (4, 4), (5, 5)])),
                ('title', models.CharField(max_length=255, verbose_name='Title', validators=[oscar.core.validators.non_whitespace])),
                ('body', models.TextField(verbose_name='Body')),
                ('name', models.CharField(max_length=255, verbose_name='Name', blank=True)),
                ('email', models.EmailField(max_length=75, verbose_name='Email', blank=True)),
                ('homepage', models.URLField(verbose_name='URL', blank=True)),
                ('status', models.SmallIntegerField(default=1, verbose_name='Status', choices=[(0, 'Requires moderation'), (1, 'Approved'), (2, 'Rejected')])),
                ('total_votes', models.IntegerField(default=0, verbose_name='Total Votes')),
                ('delta_votes', models.IntegerField(default=0, verbose_name='Delta Votes', db_index=True)),
                ('date_created', models.DateTimeField(auto_now_add=True)),
                ('product', models.ForeignKey(to='catalogue.Product', on_delete=django.db.models.deletion.SET_NULL, null=True)),
                ('user', models.ForeignKey(blank=True, to=settings.AUTH_USER_MODEL, null=True)),
            ],
            options={
                'ordering': [b'-delta_votes', b'id'],
                'abstract': False,
                'verbose_name': 'Product review',
                'verbose_name_plural': 'Product reviews',
            },
            bases=(models.Model,),
        ),
        migrations.AlterUniqueTogether(
            name='productreview',
            unique_together=set([(b'product', b'user')]),
        ),
        migrations.CreateModel(
            name='Vote',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('delta', models.SmallIntegerField(verbose_name='Delta', choices=[(1, 'Up'), (-1, 'Down')])),
                ('date_created', models.DateTimeField(auto_now_add=True)),
                ('review', models.ForeignKey(to='reviews.ProductReview')),
                ('user', models.ForeignKey(to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': [b'-date_created'],
                'abstract': False,
                'verbose_name': 'Vote',
                'verbose_name_plural': 'Votes',
            },
            bases=(models.Model,),
        ),
        migrations.AlterUniqueTogether(
            name='vote',
            unique_together=set([(b'user', b'review')]),
        ),
    ]
