# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('order', '0004_auto_20170712_1402'),
        ('offer', '0004_remove_range_classes'),
        ('basket', '0005_auto_20170712_1402'),
        ('catalogue', '0004_auto_20150217_1710'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='attributeoption',
            name='group',
        ),
        migrations.RemoveField(
            model_name='productattribute',
            name='option_group',
        ),
        migrations.RemoveField(
            model_name='productattribute',
            name='product_class',
        ),
        migrations.AlterUniqueTogether(
            name='productattributevalue',
            unique_together=set([]),
        ),
        migrations.RemoveField(
            model_name='productattributevalue',
            name='attribute',
        ),
        migrations.RemoveField(
            model_name='productattributevalue',
            name='entity_content_type',
        ),
        migrations.RemoveField(
            model_name='productattributevalue',
            name='product',
        ),
        migrations.RemoveField(
            model_name='productattributevalue',
            name='value_option',
        ),
        migrations.RemoveField(
            model_name='productclass',
            name='options',
        ),
        migrations.RemoveField(
            model_name='product',
            name='attributes',
        ),
        migrations.RemoveField(
            model_name='product',
            name='product_class',
        ),
        migrations.RemoveField(
            model_name='product',
            name='product_options',
        ),
        migrations.DeleteModel(
            name='AttributeOption',
        ),
        migrations.DeleteModel(
            name='AttributeOptionGroup',
        ),
        migrations.DeleteModel(
            name='Option',
        ),
        migrations.DeleteModel(
            name='ProductAttribute',
        ),
        migrations.DeleteModel(
            name='ProductAttributeValue',
        ),
        migrations.DeleteModel(
            name='ProductClass',
        ),
    ]
