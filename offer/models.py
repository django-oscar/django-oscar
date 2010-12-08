from django.contrib.auth.models import User
from django.db import models
from django.utils.translation import ugettext as _

class Voucher(models.Model):
    code = models.CharField(max_length=128)
    start_date = models.DateField()
    end_date = models.DateField()
    created_date = models.DateTimeField(auto_now_add=True)