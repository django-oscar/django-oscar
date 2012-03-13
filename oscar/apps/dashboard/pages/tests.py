from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django_dynamic_fixture import new, get, F

from oscar.test import ClientTestCase

from oscar.apps.dashboard.users.views import IndexView


