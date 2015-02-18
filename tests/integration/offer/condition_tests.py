from oscar.apps.offer import models
from oscar.apps.offer.utils import SetOfLines
from tests.unit.offer import OfferTest


class TestNoneCondition(OfferTest):
    def setUp(self):
        super(TestNoneCondition, self).setUp()
        self.condition = models.NoneCondition(range=self.range,
                                              type=models.Condition.NONE)
        self.set_of_lines = SetOfLines([])

    def test_is_satisfied_by_empty_set_of_lines(self):
        self.assertTrue(self.condition.is_satisfied(self.set_of_lines))
