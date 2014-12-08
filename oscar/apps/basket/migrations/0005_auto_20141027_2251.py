# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('catalogue', '0002_auto_20141027_2251'),
        ('contenttypes', '0001_initial'),
        ('basket', '0004_auto_20141007_2032'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='lineattribute',
            name='value',
        ),
        migrations.AddField(
            model_name='lineattribute',
            name='entity_content_type',
            field=models.ForeignKey(related_name=b'basket_entity_content', blank=True, editable=False, to='contenttypes.ContentType', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='lineattribute',
            name='entity_object_id',
            field=models.PositiveIntegerField(null=True, editable=False, blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='lineattribute',
            name='value_boolean',
            field=models.NullBooleanField(verbose_name='Boolean'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='lineattribute',
            name='value_date',
            field=models.DateField(null=True, verbose_name='Date', blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='lineattribute',
            name='value_file',
            field=models.FileField(max_length=255, null=True, upload_to=b'images/products/%Y/%m/', blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='lineattribute',
            name='value_float',
            field=models.FloatField(null=True, verbose_name='Float', blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='lineattribute',
            name='value_image',
            field=models.ImageField(max_length=255, null=True, upload_to=b'images/products/%Y/%m/', blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='lineattribute',
            name='value_integer',
            field=models.IntegerField(null=True, verbose_name='Integer', blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='lineattribute',
            name='value_option',
            field=models.ForeignKey(related_name=b'basket_value_option', verbose_name='Value option', blank=True, to='catalogue.AttributeOption', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='lineattribute',
            name='value_richtext',
            field=models.TextField(null=True, verbose_name='Richtext', blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='lineattribute',
            name='value_text',
            field=models.TextField(null=True, verbose_name='Text', blank=True),
            preserve_default=True,
        ),
    ]
