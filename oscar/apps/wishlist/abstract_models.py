import zlib
import datetime

from django.contrib.auth.models import User
from django.db import models
from django.utils.translation import ugettext as _
from django.core.exceptions import ObjectDoesNotExist


class AbstractWishlist(models.Model):
    u"""Wishlist object"""
    
