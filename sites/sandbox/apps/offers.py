from oscar.apps.offer import models


class ChangesOwnerName(models.Benefit):

    class Meta:
        proxy = True

    def apply(self, basket, condition, offer=None):
        condition.consume_items(basket, ())
        return models.PostOrderAction(
            "You will have your name changed to Barry!")

    @property
    def description(self):
        return "Changes owners name"
