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
                ('id', models.AutoField(auto_created=True, verbose_name='ID', primary_key=True, serialize=False)),
                ('score', models.SmallIntegerField(verbose_name='Score', choices=[(0, 0), (1, 1), (2, 2), (3, 3), (4, 4), (5, 5)])),
                ('title', models.CharField(verbose_name='Title', validators=[oscar.core.validators.non_whitespace], max_length=255)),
                ('body', models.TextField(verbose_name='Body')),
                ('name', models.CharField(verbose_name='Name', blank=True, max_length=255)),
                ('email', models.EmailField(verbose_name='Email', blank=True, max_length=75)),
                ('homepage', models.URLField(verbose_name='URL', blank=True)),
                ('status', models.SmallIntegerField(verbose_name='Status', choices=[(0, 'Requires moderation'), (1, 'Approved'), (2, 'Rejected')], default=1)),
                ('total_votes', models.IntegerField(verbose_name='Total Votes', default=0)),
                ('delta_votes', models.IntegerField(verbose_name='Delta Votes', db_index=True, default=0)),
                ('date_created', models.DateTimeField(auto_now_add=True)),
                ('product', models.ForeignKey(on_delete=django.db.models.deletion.SET_NULL, to='catalogue.Product', null=True)),
                ('user', models.ForeignKey(blank=True, to=settings.AUTH_USER_MODEL, null=True)),
            ],
            options={
                'verbose_name': 'Product review',
                'verbose_name_plural': 'Product reviews',
                'ordering': ['-delta_votes', 'id'],
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.AlterUniqueTogether(
            name='productreview',
            unique_together=set([('product', 'user')]),
        ),
        migrations.CreateModel(
            name='Vote',
            fields=[
                ('id', models.AutoField(auto_created=True, verbose_name='ID', primary_key=True, serialize=False)),
                ('delta', models.SmallIntegerField(verbose_name='Delta', choices=[(1, 'Up'), (-1, 'Down')])),
                ('date_created', models.DateTimeField(auto_now_add=True)),
                ('review', models.ForeignKey(to='reviews.ProductReview')),
                ('user', models.ForeignKey(to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Vote',
                'verbose_name_plural': 'Votes',
                'ordering': ['-date_created'],
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.AlterUniqueTogether(
            name='vote',
            unique_together=set([('user', 'review')]),
        ),
    ]
