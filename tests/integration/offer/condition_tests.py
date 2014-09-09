from mock import Mock

from oscar.apps.offer import models
from tests.unit.offer import OfferTest


class TestNoneCondition(OfferTest):
    def setUp(self):
        super(TestNoneCondition, self).setUp()
        self.condition = models.NoneCondition(range=self.range,
                                              type=models.Condition.NONE)
        self.offer = Mock()

    def test_is_satisfied_by_empty_basket(self):
        self.assertTrue(self.condition.is_satisfied(self.offer, self.basket))
