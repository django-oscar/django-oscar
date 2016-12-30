# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.db.models.deletion
import oscar.core.validators
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
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('score', models.SmallIntegerField(verbose_name='Score', choices=[(0, 0), (1, 1), (2, 2), (3, 3), (4, 4), (5, 5)])),
                ('title', models.CharField(max_length=255, verbose_name='Title', validators=[oscar.core.validators.non_whitespace])),
                ('body', models.TextField(verbose_name='Body')),
                ('name', models.CharField(max_length=255, verbose_name='Name', blank=True)),
                ('email', models.EmailField(max_length=75, verbose_name='Email', blank=True)),
                ('homepage', models.URLField(verbose_name='URL', blank=True)),
                ('status', models.SmallIntegerField(default=1, verbose_name='Status', choices=[(0, 'Requires moderation'), (1, 'Approved'), (2, 'Rejected')])),
                ('total_votes', models.IntegerField(default=0, verbose_name='Total Votes')),
                ('delta_votes', models.IntegerField(default=0, db_index=True, verbose_name='Delta Votes')),
                ('date_created', models.DateTimeField(auto_now_add=True)),
                ('product', models.ForeignKey(on_delete=django.db.models.deletion.SET_NULL, related_name='reviews', to='catalogue.Product', null=True)),
                ('user', models.ForeignKey(null=True, related_name='reviews', to=settings.AUTH_USER_MODEL, blank=True, on_delete=models.CASCADE)),
            ],
            options={
                'ordering': ['-delta_votes', 'id'],
                'verbose_name_plural': 'Product reviews',
                'verbose_name': 'Product review',
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Vote',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('delta', models.SmallIntegerField(verbose_name='Delta', choices=[(1, 'Up'), (-1, 'Down')])),
                ('date_created', models.DateTimeField(auto_now_add=True)),
                ('review', models.ForeignKey(related_name='votes', to='reviews.ProductReview', on_delete=models.CASCADE)),
                ('user', models.ForeignKey(related_name='review_votes', to=settings.AUTH_USER_MODEL, on_delete=models.CASCADE)),
            ],
            options={
                'ordering': ['-date_created'],
                'verbose_name_plural': 'Votes',
                'verbose_name': 'Vote',
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.AlterUniqueTogether(
            name='vote',
            unique_together=set([('user', 'review')]),
        ),
        migrations.AlterUniqueTogether(
            name='productreview',
            unique_together=set([('product', 'user')]),
        ),
    ]
