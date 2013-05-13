from django.test import TestCase

from oscar.core.utils import compose


class TestComposeFunction(TestCase):

    def test_composes_two_single_arg_functions(self):
        double = lambda x: 2*x
        triple = lambda x: 3*x

        f = compose(double, triple)
        self.assertEqual(f(2), 2*2*3)

    def test_composes_three_single_arg_functions(self):
        double = lambda x: 2*x
        triple = lambda x: 3*x
        quadruple = lambda x: 4*x

        f = compose(double, triple, quadruple)
        self.assertEqual(f(2), 2*2*3*4)

    def test_composes_two_multi_arg_functions(self):
        double = lambda x, y: (2*x, 2*y)
        triple = lambda x, y: (3*x, 3*y)

        f = compose(double, triple)
        self.assertEqual(f(2, 4), (2*2*3, 4*2*3))
