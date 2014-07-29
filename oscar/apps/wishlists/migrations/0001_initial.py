# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.db.models.deletion
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('catalogue', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Line',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('quantity', models.PositiveIntegerField(default=1, verbose_name='Quantity')),
                ('title', models.CharField(max_length=255, verbose_name='Title')),
                ('product', models.ForeignKey(on_delete=django.db.models.deletion.SET_NULL, verbose_name='Product', blank=True, to='catalogue.Product', null=True)),
            ],
            options={
                'abstract': False,
                'verbose_name': 'Wish list line',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='WishList',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(default='Default', max_length=255, verbose_name='Name')),
                ('key', models.CharField(verbose_name='Key', unique=True, max_length=6, editable=False, db_index=True)),
                ('visibility', models.CharField(default=b'Private', max_length=20, verbose_name='Visibility', choices=[(b'Private', 'Private - Only the owner can see the wish list'), (b'Shared', 'Shared - Only the owner and people with access to the obfuscated link can see the wish list'), (b'Public', 'Public - Everybody can see the wish list')])),
                ('date_created', models.DateTimeField(auto_now_add=True, verbose_name='Date created')),
                ('owner', models.ForeignKey(verbose_name='Owner', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': (b'owner', b'date_created'),
                'abstract': False,
                'verbose_name': 'Wish List',
            },
            bases=(models.Model,),
        ),
        migrations.AddField(
            model_name='line',
            name='wishlist',
            field=models.ForeignKey(verbose_name='Wish List', to='wishlists.WishList'),
            preserve_default=True,
        ),
        migrations.AlterUniqueTogether(
            name='line',
            unique_together=set([(b'wishlist', b'product')]),
        ),
    ]
