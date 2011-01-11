import unittest

from django.test.utils import setup_test_environment
setup_test_environment()

from django.test import TestCase
from oscar.basket.models import * 

class BasketTest(unittest.TestCase):
    def test_empty_baskets_have_zero_lines(self):
        b = Basket()
        self.assertTrue(b.get_num_lines() == 0)

if __name__ == '__main__':
    from django.test.utils import setup_test_environment
    setup_test_environment()
    unittest.main()