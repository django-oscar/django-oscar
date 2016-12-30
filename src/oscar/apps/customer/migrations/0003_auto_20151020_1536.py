# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


def forwards_func(apps, schema_editor):
    User = apps.get_model("auth", "User")

    for user in User.objects.all():
        user.emails.update(email=user.email)


class Migration(migrations.Migration):

    dependencies = [
        ('customer', '0002_auto_20151020_1533'),
    ]

    operations = [
        migrations.RunPython(forwards_func),
    ]
