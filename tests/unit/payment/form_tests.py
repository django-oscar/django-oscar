from django.test import TestCase

from oscar.apps.payment import forms


class BankcardNumberFieldTest(TestCase):

    def setUp(self):
        self.field = forms.BankcardNumberField()

    def test_spaces_are_stipped(self):
        self.assertEquals('4111111111111111', self.field.clean('  4111 1111 1111 1111'))
