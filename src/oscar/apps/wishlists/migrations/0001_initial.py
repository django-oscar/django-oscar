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
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('quantity', models.PositiveIntegerField(default=1, verbose_name='Quantity')),
                ('title', models.CharField(max_length=255, verbose_name='Title')),
                ('product', models.ForeignKey(null=True, verbose_name='Product', on_delete=django.db.models.deletion.SET_NULL, related_name='wishlists_lines', to='catalogue.Product', blank=True)),
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
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(default='Default', max_length=255, verbose_name='Name')),
                ('key', models.CharField(max_length=6, unique=True, db_index=True, verbose_name='Key', editable=False)),
                ('visibility', models.CharField(default='Private', max_length=20, verbose_name='Visibility', choices=[('Private', 'Private - Only the owner can see the wish list'), ('Shared', 'Shared - Only the owner and people with access to the obfuscated link can see the wish list'), ('Public', 'Public - Everybody can see the wish list')])),
                ('date_created', models.DateTimeField(auto_now_add=True, verbose_name='Date created')),
                ('owner', models.ForeignKey(verbose_name='Owner', related_name='wishlists', to=settings.AUTH_USER_MODEL, on_delete=models.CASCADE)),
            ],
            options={
                'ordering': ('owner', 'date_created'),
                'abstract': False,
                'verbose_name': 'Wish List',
            },
            bases=(models.Model,),
        ),
        migrations.AddField(
            model_name='line',
            name='wishlist',
            field=models.ForeignKey(verbose_name='Wish List', related_name='lines', to='wishlists.WishList', on_delete=models.CASCADE),
            preserve_default=True,
        ),
        migrations.AlterUniqueTogether(
            name='line',
            unique_together=set([('wishlist', 'product')]),
        ),
    ]
