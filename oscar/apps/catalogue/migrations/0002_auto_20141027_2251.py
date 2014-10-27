# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('catalogue', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='option',
            name='option_group',
            field=models.ForeignKey(blank=True, to='catalogue.AttributeOptionGroup', help_text='Select an option group if using type "Option"', null=True, verbose_name='Option Group'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='option',
            name='required',
            field=models.BooleanField(default=False, verbose_name='Required'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='option',
            name='type',
            field=models.CharField(default=b'text', max_length=20, verbose_name='Type', choices=[(b'text', 'Text'), (b'integer', 'Integer'), (b'boolean', 'True / False'), (b'float', 'Float'), (b'richtext', 'Rich Text'), (b'date', 'Date'), (b'option', 'Option'), (b'entity', 'Entity'), (b'file', 'File'), (b'image', 'Image')]),
        ),
    ]
