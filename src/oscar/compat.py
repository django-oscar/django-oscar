from __future__ import unicode_literals

import django
from django.db import models


if django.VERSION >= (1, 10):
    SubfieldBase = type
else:
    SubfieldBase = models.SubfieldBase
