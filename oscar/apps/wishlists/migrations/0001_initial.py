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
                ('id', models.AutoField(auto_created=True, verbose_name='ID', primary_key=True, serialize=False)),
                ('quantity', models.PositiveIntegerField(verbose_name='Quantity', default=1)),
                ('title', models.CharField(verbose_name='Title', max_length=255)),
                ('product', models.ForeignKey(verbose_name='Product', on_delete=django.db.models.deletion.SET_NULL, blank=True, to='catalogue.Product', null=True)),
            ],
            options={
                'verbose_name': 'Wish list line',
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='WishList',
            fields=[
                ('id', models.AutoField(auto_created=True, verbose_name='ID', primary_key=True, serialize=False)),
                ('name', models.CharField(verbose_name='Name', default='Default', max_length=255)),
                ('key', models.CharField(editable=False, verbose_name='Key', unique=True, db_index=True, max_length=6)),
                ('visibility', models.CharField(verbose_name='Visibility', choices=[('Private', 'Private - Only the owner can see the wish list'), ('Shared', 'Shared - Only the owner and people with access to the obfuscated link can see the wish list'), ('Public', 'Public - Everybody can see the wish list')], default='Private', max_length=20)),
                ('date_created', models.DateTimeField(verbose_name='Date created', auto_now_add=True)),
                ('owner', models.ForeignKey(verbose_name='Owner', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Wish List',
                'ordering': ('owner', 'date_created'),
                'abstract': False,
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
            unique_together=set([('wishlist', 'product')]),
        ),
    ]
