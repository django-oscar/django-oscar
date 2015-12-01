# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import oscar.models.fields.autoslugfield
import django.core.validators


class Migration(migrations.Migration):

    dependencies = [
        ('customer', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='communicationeventtype',
            name='code',
            field=oscar.models.fields.autoslugfield.AutoSlugField(populate_from=b'name', validators=[django.core.validators.RegexValidator(regex=b'^[a-zA-Z_][0-9a-zA-Z_]*$', message="Code can only contain the letters a-z, A-Z, digits, and underscores, and can't start with a digit.")], editable=False, max_length=128, separator='_', blank=True, help_text='Code used for looking up this event programmatically', unique=True, verbose_name='Code'),
            preserve_default=True,
        ),
    ]
